"""
Create the template farm, pond, and cycle cloned for new-user onboarding.

The seed is loaded from the Google Sheets-style CSV tabs in ``sample_data/``.
Run this once on the deployed backend, then set the printed ``SEEDER_*`` values
in the backend environment and restart Django.
"""

import csv
import math
from datetime import datetime
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from teramina.cost_data.models.cost_data_model import CostData
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData, ResultData
from teramina.farm.models.farm_model import Farm
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.pond.models.pond_model import Pond


POND_SIZE_M2 = 3000
DEFAULT_INITIAL_STOCKING = 360_000
ENERGY_DIVISOR = 820 * 24
SOURCE = "seed_sample"

DAILY_FIELDS = {
    "DO Morning": "do_morning",
    "DO Afternoon": "do_afternoon",
    "DO Average": "do_avg",
    "Temp Morning": "temp_morning",
    "Temp Afternoon": "temp_afternoon",
    "Temp Average": "temp_avg",
    "pH Morning": "ph_morning",
    "pH Afternoon": "ph_afternoon",
    "Salinity": "salinity",
    "NH3": "nh3",
    "Turbidity": "turbidity",
    "Feed Given": "feed_given_kg",
    "Feed Leftover": "feed_leftover",
    "Protein %": "protein_content",
    "Feeding Freq": "feeding_frequency",
}

COST_FIELDS = {
    "Benur": "seed_cost",
    "Pakan": "feeding_cost",
    "Probiotik": "probiotic_cost",
    "Tenaga Kerja": "labor_cost",
    "Panen": "harvest_cost",
    "Kimia": "other_cost",
    "Vitamin": "other_cost",
    "Lain-lain": "other_cost",
}


def _sample_data_dir() -> Path:
    candidates = [
        Path(settings.BASE_DIR) / "sample_data",
        Path(settings.BASE_DIR).parent / "sample_data",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def _read_tab(sample_dir: Path, filename: str) -> list[dict]:
    path = sample_dir / filename
    if not path.is_file():
        raise CommandError(f"Missing onboarding sample tab: {path}")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    return [row for row in rows if row.get("Date") and row["Date"] != "YYYY-MM-DD"]


def _float(value, default=0.0) -> float:
    if value in (None, "", "-", "N/A"):
        return default
    return float(value)


def _int(value, default=0) -> int:
    if value in (None, "", "-", "N/A"):
        return default
    return int(float(value))


def _load_daily_rows(sample_dir: Path) -> list[dict]:
    rows = []
    for source_row in _read_tab(sample_dir, "DAILY_LOG.csv"):
        row = {
            "date": source_row["Date"],
            "doc": _int(source_row["DOC"]),
            "feed_type": source_row["Feed Type"],
            "notes": source_row["Notes"],
            "source": SOURCE,
        }
        for source_key, target_key in DAILY_FIELDS.items():
            value = _int(source_row[source_key]) if target_key == "feeding_frequency" else _float(source_row[source_key])
            row[target_key] = value
        rows.append(row)

    return rows


def _merge_sampling_tabs(sample_dir: Path, daily_rows: list[dict]) -> None:
    rows_by_doc = {row["doc"]: row for row in daily_rows}

    for row in _read_tab(sample_dir, "ABW_SAMPLING.csv"):
        target = rows_by_doc[_int(row["DOC"])]
        target.update(
            {
                "abw_sample_count": _int(row["Sample Count"]),
                "abw_total_weight_g": _float(row["Total Weight (g)"]),
                "abw": _float(row["ABW (g)"]),
                "abw_min_g": _float(row["Min Weight"]),
                "abw_max_g": _float(row["Max Weight"]),
                "abw_cv_pct": _float(row["CV%"]),
                "sampled_by": row["Sampled By"],
                "abw_notes": row["Notes"],
            }
        )

    for row in _read_tab(sample_dir, "MORTALITY.csv"):
        rows_by_doc[_int(row["DOC"])].update(
            {
                "mortality_count": _int(row["Dead Count"]),
                "mortality_notes": row["Notes"],
            }
        )


def _load_cost_rows(sample_dir: Path) -> list[dict]:
    return [
        {
            "date": row["Date"],
            "category": row["Category"],
            "description": row["Description"],
            "quantity": _float(row["Quantity"]),
            "unit": row["Unit"],
            "unit_price": _float(row["Unit Price (IDR)"]),
            "total": _float(row["Total (IDR)"]),
            "vendor": row["Vendor"],
            "notes": row["Notes"],
            "source": SOURCE,
        }
        for row in _read_tab(sample_dir, "COST.csv")
    ]


def _load_harvest_data(sample_dir: Path) -> tuple[dict, dict[int, dict]]:
    harvest_data = {
        "partial1": {"doc": "", "biomass": "", "revenue": ""},
        "partial2": {"doc": "", "biomass": "", "revenue": ""},
        "partial3": {"doc": "", "biomass": "", "revenue": ""},
        "final": {"doc": "", "biomass": "", "revenue": ""},
    }
    events = {}
    partial_number = 1

    for row in _read_tab(sample_dir, "HARVEST.csv"):
        doc = _int(row["DOC"])
        biomass = _float(row["Biomass (kg)"])
        price = _float(row["Price/kg (IDR)"])
        is_partial = row["Is Partial?"].strip().upper() in {"Y", "YES", "TRUE", "1"}
        key = f"partial{partial_number}" if is_partial else "final"
        if is_partial:
            partial_number += 1

        event = {
            "date": row["Date"],
            "doc": doc,
            "biomass": biomass,
            "revenue": biomass * price,
            "is_partial": is_partial,
            "abw_g": _float(row["ABW at Harvest (g)"]),
            "sr_pct": _float(row["SR at Harvest (%)"]),
            "bags": _int(row["Bags"]),
            "buyer": row["Buyer"],
            "price_per_kg_idr": price,
            "notes": row["Notes"],
            "source": SOURCE,
        }
        harvest_data[key] = event
        events[doc] = event

    return harvest_data, events


def _build_costs_by_doc(daily_rows: list[dict], cost_rows: list[dict]) -> tuple[dict[int, dict], int]:
    date_to_doc = {row["date"]: row["doc"] for row in daily_rows}
    costs_by_doc = {
        row["doc"]: {
            "seed_cost": 0.0,
            "feeding_cost": 0.0,
            "probiotic_cost": 0.0,
            "labor_cost": 0.0,
            "bonus_cost": 0.0,
            "energy_cost": 0.0,
            "harvest_cost": 0.0,
            "other_cost": 0.0,
        }
        for row in daily_rows
    }
    initial_stocking = DEFAULT_INITIAL_STOCKING

    for row in cost_rows:
        doc = date_to_doc[row["date"]]
        category = row["category"]
        total = row["total"]
        if category == "Benur":
            initial_stocking = _int(row["quantity"], DEFAULT_INITIAL_STOCKING)
        if category == "Utilitas":
            costs_by_doc[doc]["energy_cost"] += total / ENERGY_DIVISOR
        elif category in COST_FIELDS:
            costs_by_doc[doc][COST_FIELDS[category]] += total

    return costs_by_doc, initial_stocking


def _build_interpolated_series(daily_rows: list[dict], harvest_events: dict[int, dict]) -> tuple[pd.Series, pd.Series]:
    max_doc = daily_rows[-1]["doc"]

    abw = pd.Series(index=range(1, max_doc + 1), dtype=float)
    abw.loc[1] = 0.02
    for row in daily_rows:
        if "abw" in row:
            abw.loc[row["doc"]] = row["abw"]
    for doc, event in harvest_events.items():
        abw.loc[doc] = event["abw_g"]
    abw = abw.interpolate().ffill().bfill()

    sr = pd.Series(index=range(0, max_doc + 1), dtype=float)
    sr.loc[0] = 1.0
    for doc, event in harvest_events.items():
        sr.loc[doc] = event["sr_pct"] / 100
    sr = sr.interpolate().ffill().bfill().loc[1:]

    return abw, sr


def _build_result_rows(
    daily_rows: list[dict],
    cost_rows: list[dict],
    harvest_events: dict[int, dict],
) -> list[dict]:
    costs_by_doc, initial_stocking = _build_costs_by_doc(daily_rows, cost_rows)
    abw_by_doc, sr_by_doc = _build_interpolated_series(daily_rows, harvest_events)

    result_rows = []
    cumulative_feed = 0.0
    cumulative_cost = 0.0
    cumulative_revenue = 0.0
    cumulative_harvest = 0.0
    harvested_population = 0.0
    previous_abw = None

    for raw in daily_rows:
        doc = raw["doc"]
        abw = float(abw_by_doc.loc[doc])
        sr = float(sr_by_doc.loc[doc])
        event = harvest_events.get(doc)
        harvest_biomass = event["biomass"] if event else 0.0
        harvest_population = harvest_biomass * 1000 / abw if harvest_biomass else 0.0
        harvested_population += harvest_population

        population = max(initial_stocking * sr - harvested_population, 0.0)
        biomass = population * abw / 1000
        cumulative_harvest += harvest_biomass
        total_biomass = biomass + cumulative_harvest

        feed_given = raw["feed_given_kg"]
        cumulative_feed += feed_given
        fr = feed_given / biomass * 100 if biomass else 0.0
        fcr = cumulative_feed / total_biomass if total_biomass else 0.0

        costs = costs_by_doc[doc]
        cost_energy = costs["energy_cost"] * ENERGY_DIVISOR
        total_cost = sum(value for key, value in costs.items() if key != "energy_cost") + cost_energy
        cumulative_cost += total_cost

        realized_revenue = event["revenue"] if event else 0.0
        cumulative_revenue += realized_revenue
        price = event["price_per_kg_idr"] if event else 58_000.0
        potential_revenue = biomass * price
        profit = cumulative_revenue - cumulative_cost
        adg = abw - previous_abw if previous_abw is not None else 0.0
        sgr = math.log(abw / previous_abw) * 100 if previous_abw else 0.0
        previous_abw = abw

        result_rows.append(
            {
                "date": datetime.strptime(raw["date"], "%Y-%m-%d"),
                "doc": doc,
                "temperature": raw["temp_avg"],
                "do": raw["do_avg"],
                "nh3": raw["nh3"],
                "ph_morning": raw["ph_morning"],
                "ph_afternoon": raw["ph_afternoon"],
                "salinity": raw["salinity"],
                "turbidity": raw["turbidity"],
                "abw": abw,
                "adj_abw": abw,
                "adg": adg,
                "sgr": sgr,
                "fr": fr,
                "adj_fr": fr / 100,
                "sr": sr,
                "w0": 0.02,
                "initial_stocking": initial_stocking,
                "population": population,
                "harvest_population": harvest_population,
                "biomass_kg": biomass,
                "origin_biomass": biomass,
                "harvest_biomass_kg": harvest_biomass,
                "total_biomass": total_biomass,
                "feed_given": feed_given,
                "cum_feed": cumulative_feed,
                "fcr": fcr,
                "realized_fcr": fcr,
                "protein_content": raw["protein_content"],
                "seed_cost": costs["seed_cost"],
                "feeding_cost": costs["feeding_cost"],
                "probiotic_cost": costs["probiotic_cost"],
                "labor_cost": costs["labor_cost"],
                "bonus_cost": costs["bonus_cost"],
                "energy_cost": costs["energy_cost"],
                "harvest_cost": costs["harvest_cost"],
                "other_cost": costs["other_cost"],
                "cost_seed": costs["seed_cost"],
                "cost_feed": costs["feeding_cost"],
                "cost_probiotics": costs["probiotic_cost"],
                "cost_labor": costs["labor_cost"],
                "cost_bonuss": costs["bonus_cost"],
                "cost_energy": cost_energy,
                "cost_harvest": costs["harvest_cost"],
                "cost_other": costs["other_cost"],
                "total_cost": total_cost,
                "cum_total_cost": cumulative_cost,
                "cost_per_kg": cumulative_cost / total_biomass if total_biomass else 0.0,
                "realized_revenue": realized_revenue,
                "cum_realized_revenue": cumulative_revenue,
                "potential_revenue": potential_revenue,
                "profit": profit,
                "potential_profit": profit + potential_revenue,
                "chb": potential_revenue,
                "category": "historical",
                "source": SOURCE,
            }
        )

    return result_rows


def load_sample_seed_data(sample_dir: Path | None = None) -> dict:
    sample_dir = sample_dir or _sample_data_dir()
    daily_rows = _load_daily_rows(sample_dir)
    if len(daily_rows) != 120:
        raise CommandError(f"Expected 120 DAILY_LOG rows, found {len(daily_rows)}")

    _merge_sampling_tabs(sample_dir, daily_rows)
    cost_rows = _load_cost_rows(sample_dir)
    harvest_data, harvest_events = _load_harvest_data(sample_dir)
    result_rows = _build_result_rows(daily_rows, cost_rows, harvest_events)
    feed_rows = [
        {
            "doc": row["doc"],
            "ration_number": 0,
            "feed_ration": row["feed_given_kg"],
            "feed_given": row["feed_given_kg"],
            "feed_leftover": row["feed_leftover"],
        }
        for row in daily_rows
    ]

    return {
        "daily_rows": daily_rows,
        "result_rows": result_rows,
        "feed_rows": feed_rows,
        "cost_rows": cost_rows,
        "harvest_data": harvest_data,
        "start_date": datetime.strptime(daily_rows[0]["date"], "%Y-%m-%d"),
    }


class Command(BaseCommand):
    help = "Seed the Google Sheets-style demo cycle cloned during new-user onboarding"

    def handle(self, *args, **options):
        self.stdout.write(f"Loading onboarding seed from {_sample_data_dir()}...")
        seed = load_sample_seed_data()
        now = datetime.utcnow()

        farm = Farm(name="Demo Farm", location="Jawa Timur", user_id="__seed__")
        farm.save()
        farm_id = str(farm.id)

        pond = Pond(
            name="Kolam Demo 1",
            size=float(POND_SIZE_M2),
            depth=1.5,
            pond_construction="Tambak tanah",
            pond_shape="Persegi",
            farm_id=farm_id,
        )
        pond.save()
        pond_id = str(pond.id)

        cycle = Cycle(
            name="Siklus Demo 120 Hari",
            start_date=seed["start_date"],
            pond_id=pond_id,
            last_updated=now,
            is_active=False,
        )
        cycle.save()
        cycle_id = str(cycle.id)

        pond.active_cycle_id = cycle_id
        pond.save()

        CycleData(cycle_id=cycle_id, result_data=seed["daily_rows"], last_updated=now).save()
        ResultData(cycle_id=cycle_id, result_data=seed["result_rows"], last_updated=now).save()
        ForecastData(cycle_id=cycle_id, result_data=seed["result_rows"], last_updated=now).save()

        for row in seed["feed_rows"]:
            FeedRealization(cycle_id=cycle_id, last_updated=now, **row).save()

        HarvestRecord(cycle_id=cycle_id, harvest_data=seed["harvest_data"], last_updated=now).save()
        CostData(
            farm_id=cycle_id,
            start_date=seed["daily_rows"][0]["date"],
            end_date=seed["daily_rows"][-1]["date"],
            data=seed["cost_rows"],
            last_updated=now,
        ).save()

        self.stdout.write(f"Farm created:  {farm_id}")
        self.stdout.write(f"Pond created:  {pond_id}")
        self.stdout.write(f"Cycle created: {cycle_id}")
        self.stdout.write(f"Daily/derived rows: {len(seed['daily_rows'])}/{len(seed['result_rows'])}")
        self.stdout.write(f"Feed/cost rows:     {len(seed['feed_rows'])}/{len(seed['cost_rows'])}")
        self.stdout.write("\nAdd these to the deployed backend environment:")
        self.stdout.write(f"SEEDER_FARM={farm_id}")
        self.stdout.write(f"SEEDER_POND={pond_id}")
        self.stdout.write(f"SEEDER_CYCLE={cycle_id}")
        self.stdout.write("Done. New users will receive this sample cycle on first login.")

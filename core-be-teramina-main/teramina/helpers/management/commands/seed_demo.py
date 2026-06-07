"""
Create the template farm, pond, and cycle cloned for new-user onboarding.

The seed is loaded from the Google Sheets-style CSV tabs in ``sample_data/``.
Run this once on the deployed backend, then set the printed ``SEEDER_*`` values
in the backend environment and restart Django.
"""

import csv
import copy
import math
from datetime import date, datetime, timedelta
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
from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.pond.models.pond_model import Pond
from teramina.water_quality_dashboard.services.variable_management import VariableManagement


POND_SIZE_M2 = 3000
DEFAULT_INITIAL_STOCKING = 360_000
ENERGY_DIVISOR = 820 * 24
SOURCE = "seed_sample"
DEMO_BUNDLE_VERSION = "abw-v2"
CURRENT_DOC = 60
SCENARIOS = (
    {
        "key": "healthy",
        "pond_name": "Scenario A - Healthy",
        "cycle_name": "Scenario A - Healthy Active",
    },
    {
        "key": "at_risk",
        "pond_name": "Scenario B - At Risk",
        "cycle_name": "Scenario B - At-Risk Active",
    },
)

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
                "feed_ration_1": fr / 400,
                "feed_ration_2": fr / 400,
                "feed_ration_3": fr / 400,
                "feed_ration_4": fr / 400,
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
    result_by_doc = {row["doc"]: row for row in result_rows}
    feed_rows = [
        {
            "doc": row["doc"],
            "ration_number": 1,
            "feed_ration": result_by_doc[row["doc"]]["fr"],
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


def build_demo_scenario(seed: dict, scenario_key: str, today: date | None = None) -> dict:
    """Build one rolling active scenario from the canonical 120-day CSV sample."""
    today = today or date.today()
    start_date = datetime.combine(today - timedelta(days=CURRENT_DOC - 1), datetime.min.time())
    original_date_to_doc = {row["date"]: row["doc"] for row in seed["daily_rows"]}

    daily_rows = copy.deepcopy(seed["daily_rows"])
    result_rows = copy.deepcopy(seed["result_rows"])
    feed_rows = copy.deepcopy(seed["feed_rows"])
    cost_rows = copy.deepcopy(seed["cost_rows"])

    for row in daily_rows:
        row["date"] = (start_date + timedelta(days=row["doc"] - 1)).strftime("%Y-%m-%d")
        row["demo_scenario"] = scenario_key
        if scenario_key == "at_risk" and row["doc"] >= 45:
            progress = (row["doc"] - 44) / 76
            row["do_morning"] = round(max(1.8, row["do_morning"] - 2.8 * progress), 2)
            row["do_afternoon"] = round(max(2.1, row["do_afternoon"] - 2.4 * progress), 2)
            row["do_avg"] = round((row["do_morning"] + row["do_afternoon"]) / 2, 2)
            row["nh3"] = round(row["nh3"] + 0.55 * progress, 3)
            row["feed_leftover"] = round(max(row["feed_leftover"], row["feed_given_kg"] * 0.28), 2)
            row["notes"] = "At-risk scenario: oxygen pressure, elevated ammonia, and feed leftovers."

    for row in result_rows:
        row["date"] = start_date + timedelta(days=row["doc"] - 1)
        row["category"] = "historical" if row["doc"] <= CURRENT_DOC else "forecast"
        row["demo_scenario"] = scenario_key
        row["biomass"] = row["biomass_kg"]
        if scenario_key == "at_risk" and row["doc"] >= 45:
            progress = (row["doc"] - 44) / 76
            growth_factor = 1 - (0.22 * progress)
            survival_factor = 1 - (0.12 * progress)
            row["do"] = round(max(1.8, row["do"] - 2.8 * progress), 2)
            row["nh3"] = round(row["nh3"] + 0.55 * progress, 3)
            row["abw"] *= growth_factor
            row["adj_abw"] *= growth_factor
            row["sr"] *= survival_factor
            for field in ("population", "biomass_kg", "origin_biomass", "total_biomass", "biomass"):
                row[field] *= growth_factor * survival_factor
            row["fcr"] *= 1 + (0.35 * progress)
            row["realized_fcr"] = row["fcr"]
            row["cum_total_cost"] *= 1 + (0.18 * progress)
            row["cost_per_kg"] = row["cum_total_cost"] / row["total_biomass"] if row["total_biomass"] else 0
            row["potential_revenue"] *= growth_factor * survival_factor
            row["potential_profit"] = row["profit"] + row["potential_revenue"] - (row["cum_total_cost"] * 0.18 * progress)
            row["profit"] -= row["cum_total_cost"] * 0.18 * progress

    for row in feed_rows:
        if scenario_key == "at_risk" and row["doc"] >= 45:
            row["feed_leftover"] = round(max(row["feed_leftover"], row["feed_given"] * 0.28), 2)

    shifted_cost_rows = []
    for row in cost_rows:
        doc = original_date_to_doc[row["date"]]
        if doc > CURRENT_DOC:
            continue
        row["date"] = (start_date + timedelta(days=doc - 1)).strftime("%Y-%m-%d")
        row["demo_scenario"] = scenario_key
        if scenario_key == "at_risk" and row["category"] in {"Pakan", "Probiotik", "Kimia", "Vitamin"}:
            row["total"] = round(row["total"] * 1.18, 2)
            row["unit_price"] = round(row["total"] / row["quantity"], 2) if row["quantity"] else row["unit_price"]
        shifted_cost_rows.append(row)

    empty_harvest = {
        "partial1": {"doc": "", "biomass": "", "revenue": ""},
        "partial2": {"doc": "", "biomass": "", "revenue": ""},
        "partial3": {"doc": "", "biomass": "", "revenue": ""},
        "final": {"doc": "", "biomass": "", "revenue": ""},
    }
    recommendation = {
        "partial1": {"doc": 90 if scenario_key == "healthy" else 78, "biomass": 20},
        "partial2": {"doc": "", "biomass": ""},
        "partial3": {"doc": "", "biomass": ""},
        "final": {"doc": 110 if scenario_key == "healthy" else 96, "biomass": ""},
    }

    return {
        "start_date": start_date,
        "daily_rows": daily_rows[:CURRENT_DOC],
        "result_rows": result_rows[:CURRENT_DOC],
        "forecast_rows": result_rows,
        "feed_rows": feed_rows[:CURRENT_DOC],
        "cost_rows": shifted_cost_rows,
        "harvest_data": empty_harvest,
        "harvest_recommendation": recommendation,
    }


def _delete_seed_templates():
    """Remove existing template bundles and their child documents before reseeding."""
    for farm in Farm.objects(user_id="__seed__"):
        for pond in Pond.objects(farm_id=str(farm.id)):
            for cycle in Cycle.objects(pond_id=str(pond.id)):
                cycle_id = str(cycle.id)
                CycleData.objects(cycle_id=cycle_id).delete()
                ResultData.objects(cycle_id=cycle_id).delete()
                ForecastData.objects(cycle_id=cycle_id).delete()
                FeedRealization.objects(cycle_id=cycle_id).delete()
                HarvestRecord.objects(cycle_id=cycle_id).delete()
                HarvestRecommendation.objects(cycle_id=cycle_id).delete()
                CostData.objects(farm_id=cycle_id).delete()
                cycle.delete()
            pond.delete()
        farm.delete()


class Command(BaseCommand):
    help = "Seed the Google Sheets-style demo cycle cloned during new-user onboarding"

    def handle(self, *args, **options):
        self.stdout.write(f"Loading onboarding seed from {_sample_data_dir()}...")
        VariableManagement().ensure_default_variables()
        seed = load_sample_seed_data()
        now = datetime.utcnow()
        _delete_seed_templates()

        farm = Farm(
            name="Demo A/B Farm",
            location="Jawa Timur",
            user_id="__seed__",
            demo_bundle_version=DEMO_BUNDLE_VERSION,
        )
        farm.save()
        farm_id = str(farm.id)
        first_pond_id = first_cycle_id = ""
        for scenario in SCENARIOS:
            scenario_data = build_demo_scenario(seed, scenario["key"])
            pond = Pond(
                name=scenario["pond_name"],
                size=float(POND_SIZE_M2),
                depth=1.5,
                pond_construction="Tambak tanah",
                pond_shape="Persegi",
                farm_id=farm_id,
                demo_scenario=scenario["key"],
            ).save()
            cycle = Cycle(
                name=scenario["cycle_name"],
                start_date=scenario_data["start_date"],
                pond_id=str(pond.id),
                demo_scenario=scenario["key"],
                last_updated=now,
                is_active=True,
            ).save()
            cycle_id = str(cycle.id)
            pond.active_cycle_id = cycle_id
            pond.save()

            CycleData(cycle_id=cycle_id, result_data=scenario_data["daily_rows"], last_updated=now).save()
            ResultData(cycle_id=cycle_id, result_data=scenario_data["result_rows"], last_updated=now).save()
            ForecastData(cycle_id=cycle_id, result_data=scenario_data["forecast_rows"], last_updated=now).save()
            for row in scenario_data["feed_rows"]:
                FeedRealization(cycle_id=cycle_id, last_updated=now, **row).save()
            HarvestRecord(cycle_id=cycle_id, harvest_data=scenario_data["harvest_data"], last_updated=now).save()
            HarvestRecommendation(
                cycle_id=cycle_id,
                harvest_data=scenario_data["harvest_recommendation"],
                last_updated=now,
            ).save()
            CostData(
                farm_id=cycle_id,
                start_date=scenario_data["daily_rows"][0]["date"],
                end_date=scenario_data["daily_rows"][-1]["date"],
                data=scenario_data["cost_rows"],
                last_updated=now,
            ).save()
            first_pond_id = first_pond_id or str(pond.id)
            first_cycle_id = first_cycle_id or cycle_id
            self.stdout.write(
                f"{scenario['pond_name']}: historical={len(scenario_data['daily_rows'])} "
                f"forecast={len(scenario_data['forecast_rows'])}"
            )

        self.stdout.write(f"Farm created:  {farm_id}")
        self.stdout.write("\nAdd these to the deployed backend environment:")
        self.stdout.write(f"SEEDER_FARM={farm_id}")
        self.stdout.write(f"SEEDER_POND={first_pond_id}")
        self.stdout.write(f"SEEDER_CYCLE={first_cycle_id}")
        self.stdout.write("Done. New users will receive this synchronized A/B demo bundle on first login.")

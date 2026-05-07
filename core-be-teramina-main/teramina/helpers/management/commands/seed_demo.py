"""
Management command: seed_demo
-----------------------------
Creates the template farm/pond/cycle that every new user gets cloned on
first login. Run this once on the server where MongoDB Atlas is reachable.

Usage:
    python manage.py seed_demo

After running, copy the three printed env vars into your .env file:
    SEEDER_FARM=<id>
    SEEDER_POND=<id>
    SEEDER_CYCLE=<id>

Then restart Django so the env vars are picked up.
"""

import math
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData, ResultData, ForecastData
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.cost_data.models.cost_data_model import CostData


POND_SIZE_M2     = 3000
INITIAL_STOCKING = 360_000
START_DATE       = datetime(2024, 3, 1)
TOTAL_DAYS       = 120
PARTIAL_DOC      = 95
PARTIAL_FRACTION = 0.30

ABW_CHECKPOINTS = {
    0: 0.001, 7: 0.8, 14: 1.5, 21: 2.8, 28: 4.5,
    35: 6.8, 42: 9.5, 50: 12.5, 60: 15.8, 70: 18.9,
    80: 21.7, 90: 24.2, 95: 25.6, 100: 26.8, 110: 28.9, 120: 30.5,
}

FEED_SCHEDULE = [
    (1,  14, "Tipe 00", 38, 18_000),
    (15, 30, "Tipe 0",  36, 17_000),
    (31, 60, "Tipe 1",  35, 15_500),
    (61, 90, "Tipe 2",  34, 14_000),
    (91, 120, "Tipe 3", 32, 13_000),
]


def shrimp_price(abw_g):
    if abw_g < 10:  return 42_000
    if abw_g < 15:  return 50_000
    if abw_g < 20:  return 55_000
    if abw_g < 25:  return 62_000
    if abw_g < 30:  return 70_000
    return 78_000


def interp_abw(doc):
    keys = sorted(ABW_CHECKPOINTS)
    if doc <= keys[0]:  return ABW_CHECKPOINTS[keys[0]]
    if doc >= keys[-1]: return ABW_CHECKPOINTS[keys[-1]]
    for i in range(len(keys) - 1):
        d0, d1 = keys[i], keys[i + 1]
        if d0 <= doc <= d1:
            t = (doc - d0) / (d1 - d0)
            return ABW_CHECKPOINTS[d0] + t * (ABW_CHECKPOINTS[d1] - ABW_CHECKPOINTS[d0])
    return ABW_CHECKPOINTS[keys[-1]]


def feed_info(doc):
    for d0, d1, name, prot, cost in FEED_SCHEDULE:
        if d0 <= doc <= d1:
            return name, prot, cost
    return "Tipe 3", 32, 13_000


def jitter(val, pct=0.03):
    return val * (1 + random.uniform(-pct, pct))


def cum_mortality(doc):
    if doc <= 14:  return 0.04 * (doc / 14)
    if doc <= 60:  return 0.04 + 0.14 * ((doc - 14) / 46)
    if doc <= 95:  return 0.18 + 0.05 * ((doc - 60) / 35)
    return 0.23 + 0.04 * ((doc - 95) / 25)


def generate_daily_data():
    random.seed(42)

    result_rows = []
    feed_rows = []
    cost_rows = []
    harvest_events = []  # list of {doc, biomass_kg, price, is_partial}

    for doc in range(1, TOTAL_DAYS + 1):
        date = START_DATE + timedelta(days=doc - 1)
        date_str = date.strftime("%Y-%m-%d")

        abw = interp_abw(doc)
        sr_total = 1.0 - cum_mortality(doc)
        population = round(INITIAL_STOCKING * sr_total)
        biomass_kg = population * abw / 1000.0

        do_m  = jitter(6.8);  do_a  = jitter(5.9);  do_avg  = (do_m + do_a) / 2
        tmp_m = jitter(28.5); tmp_a = jitter(30.2);  tmp_avg = (tmp_m + tmp_a) / 2
        ph_m  = jitter(7.9, 0.01); ph_a = jitter(8.1, 0.01)
        sal   = jitter(28.0, 0.02)
        nh3   = max(0.001, jitter(0.02, 0.4))
        turb  = max(15, jitter(35.0, 0.2))

        feed_pct = max(2.5, 8.0 - 0.045 * doc)
        feed_kg = round(biomass_kg * feed_pct / 100, 2)
        feed_leftover = round(jitter(feed_kg * 0.04, 0.5), 2)
        freq = 4 if doc <= 30 else (5 if doc <= 70 else 6)
        fname, fprot, fcost_idr = feed_info(doc)

        feed_cost_day = feed_kg * fcost_idr
        labor_cost_day = 500_000 / 30
        energy_cost_day = 800_000 / 30
        probiotic_day = 200_000 / 30 if doc % 3 == 0 else 0
        other_day = 50_000 / 30

        is_partial_harvest = (doc == PARTIAL_DOC)
        is_final_harvest = (doc == TOTAL_DAYS)

        if is_partial_harvest:
            harvest_pop = round(population * PARTIAL_FRACTION)
            harvest_kg = round(harvest_pop * abw / 1000, 2)
            price = shrimp_price(abw)
            harvest_events.append({"doc": doc, "biomass_kg": harvest_kg, "price": price, "is_partial": True})

        if is_final_harvest:
            remaining_pop = round(population * (1 - PARTIAL_FRACTION))
            harvest_kg = round(remaining_pop * abw / 1000, 2)
            price = shrimp_price(abw)
            harvest_events.append({"doc": doc, "biomass_kg": harvest_kg, "price": price, "is_partial": False})

        abw_entry = {}
        if doc >= 14 and (doc - 14) % 7 == 0:
            sample_n = 100
            abw_entry = {
                "abw": round(abw, 2), "abw_sample_count": sample_n,
                "abw_total_weight_g": round(abw * sample_n, 1),
                "abw_min_g": round(abw * 0.75, 2), "abw_max_g": round(abw * 1.28, 2),
                "abw_cv_pct": round(random.uniform(15, 25), 1),
                "sampled_by": "Teknisi", "abw_notes": "",
            }

        prev_sr = 1.0 - cum_mortality(doc - 1) if doc > 1 else 1.0
        prev_pop = round(INITIAL_STOCKING * prev_sr)
        daily_dead = max(0, prev_pop - population)

        result_rows.append({
            "date": date_str, "doc": doc,
            "do_morning": round(do_m, 2), "do_afternoon": round(do_a, 2), "do_avg": round(do_avg, 2),
            "temp_morning": round(tmp_m, 2), "temp_afternoon": round(tmp_a, 2), "temp_avg": round(tmp_avg, 2),
            "ph_morning": round(ph_m, 2), "ph_afternoon": round(ph_a, 2),
            "salinity": round(sal, 1), "nh3": round(nh3, 4), "turbidity": round(turb, 1),
            "feed_given_kg": feed_kg, "feed_leftover": feed_leftover,
            "feed_type": fname, "protein_content": float(fprot), "feeding_frequency": freq,
            "mortality_count": daily_dead, "mortality_notes": "", "notes": "", "source": "seed",
            **abw_entry,
        })

        feed_rows.append({
            "doc": doc, "ration_number": 0,
            "feed_ration": feed_kg, "feed_given": feed_kg, "feed_leftover": feed_leftover,
        })

        if doc % 30 == 1:
            month_label = f"Bulan {(doc // 30) + 1}"
            cost_rows.extend([
                {"date": date_str, "category": "Feed", "description": f"Pakan {fname}", "quantity": feed_kg * 30, "unit": "kg", "unit_price": fcost_idr, "total": feed_kg * 30 * fcost_idr, "vendor": "CV Pakan Maju", "notes": month_label, "source": "seed"},
                {"date": date_str, "category": "Labor", "description": "Upah tenaga kerja", "quantity": 1, "unit": "bulan", "unit_price": 500_000, "total": 500_000, "vendor": "", "notes": month_label, "source": "seed"},
                {"date": date_str, "category": "Electricity", "description": "Listrik aerasi", "quantity": 1, "unit": "bulan", "unit_price": 800_000, "total": 800_000, "vendor": "PLN", "notes": month_label, "source": "seed"},
                {"date": date_str, "category": "Chemical", "description": "Probiotik & suplemen", "quantity": 10, "unit": "L", "unit_price": 20_000, "total": 200_000, "vendor": "Toko Tambak Jaya", "notes": month_label, "source": "seed"},
            ])

    result_computed = []
    cum_feed = 0.0
    cum_cost = 0.0
    cum_rev = 0.0
    for row in result_rows:
        doc = row["doc"]
        abw = row.get("abw", interp_abw(doc))
        sr_total = 1.0 - cum_mortality(doc)
        pop = round(INITIAL_STOCKING * sr_total)
        biomass = pop * abw / 1000.0
        feed = row["feed_given_kg"]
        fname, fprot, fcost_idr = feed_info(doc)
        feed_cost_d = feed * fcost_idr
        # Daily cost values — units must match what cost_formula.py expects:
        # energy_cost: rate multiplied by AERATOR_WATTS(820) × HOURS_PER_DAY(24) → IDR/day
        #   12 × 820 × 24 = 235,520 IDR/day (realistic for a 3000m² aerated pond)
        # feeding_cost, labor_cost, probiotic_cost, other_cost: direct IDR/day values
        energy_rate = 12.0
        labor_day = round(500_000 / 30, 0)
        probiotic_day = round(200_000 / 30, 0) if doc % 3 == 0 else 0.0
        other_day = round(50_000 / 30, 0)
        energy_day = energy_rate * 820 * 24
        total_cost_d = feed_cost_d + labor_day + energy_day + probiotic_day + other_day
        rev = sum(hr["harvest_biomass_kg"] * hr["price_per_kg_idr"] for hr in harvest_records if hr["doc"] == doc)
        cum_feed += feed
        cum_cost += total_cost_d
        cum_rev += rev
        result_computed.append({
            "date": row["date"], "doc": doc,
            "temperature": row["temp_avg"], "do": row["do_avg"], "nh3": row["nh3"],
            "abw": round(abw, 2),
            "fr": round(feed / biomass * 100, 2) if biomass > 0 else 0,
            "sr": round(sr_total * 100, 2),
            "w0": 0.001, "initial_stocking": INITIAL_STOCKING,
            "total_biomass": round(biomass, 2),
            "feed_given": feed, "total_cost": round(total_cost_d, 0),
            "realized_revenue": round(rev, 0),
            "cum_feed": round(cum_feed, 2),
            "fcr": round(cum_feed / biomass, 3) if biomass > 0 else 0,
            "cum_total_cost": round(cum_cost, 0),
            "cost_per_kg": round(cum_cost / biomass, 0) if biomass > 0 else 0,
            "cum_realized_revenue": round(cum_rev, 0),
            "profit": round(cum_rev - cum_cost, 0),
            "labor_cost": labor_day, "bonus_cost": 0.0, "energy_cost": energy_rate,
            "probiotic_cost": probiotic_day, "other_cost": other_day, "harvest_cost": 0.0,
            "feeding_cost": round(feed_cost_d, 0),
            "protein_content": float(fprot),
            "chb": round(biomass * shrimp_price(abw), 0),
            "source": "seed",
        })

    # Build canonical HarvestRecord structure expected by harvest_service / forecast_service:
    # {"final": {doc, biomass, revenue}, "partial1": {...}, "partial2": {...}, "partial3": {...}}
    partials = [e for e in harvest_events if e["is_partial"]]
    final_ev = next((e for e in harvest_events if not e["is_partial"]), None)

    harvest_data = {
        "partial1": {"doc": "", "biomass": "", "revenue": ""},
        "partial2": {"doc": "", "biomass": "", "revenue": ""},
        "partial3": {"doc": "", "biomass": "", "revenue": ""},
        "final":    {"doc": "", "biomass": "", "revenue": ""},
    }
    for i, ev in enumerate(partials[:3], start=1):
        harvest_data[f"partial{i}"] = {
            "doc": ev["doc"],
            "biomass": ev["biomass_kg"],
            "revenue": round(ev["biomass_kg"] * ev["price"], 0),
        }
    if final_ev:
        harvest_data["final"] = {
            "doc": final_ev["doc"],
            "biomass": final_ev["biomass_kg"],
            "revenue": round(final_ev["biomass_kg"] * final_ev["price"], 0),
        }

    return result_rows, result_computed, feed_rows, cost_rows, harvest_data


class Command(BaseCommand):
    help = "Seed demo farm/pond/cycle template for new-user onboarding"

    def handle(self, *args, **options):
        self.stdout.write("Generating 120-day demo data...")
        result_rows, result_computed, feed_rows, cost_rows, harvest_data = generate_daily_data()

        self.stdout.write(f"  Daily rows:     {len(result_rows)}")
        self.stdout.write(f"  Feed rows:      {len(feed_rows)}")
        self.stdout.write(f"  Cost entries:   {len(cost_rows)}")

        now = datetime.utcnow()

        farm = Farm(name="Demo Farm", location="Jawa Timur", user_id="__seed__")
        farm.save()
        farm_id = str(farm.id)
        self.stdout.write(f"Farm created:  {farm_id}")

        pond = Pond(
            name="Kolam Demo 1", size=float(POND_SIZE_M2), depth=1.5,
            pond_construction="Tambak tanah", pond_shape="Persegi", farm_id=farm_id,
        )
        pond.save()
        pond_id = str(pond.id)
        self.stdout.write(f"Pond created:  {pond_id}")

        cycle = Cycle(
            name="Siklus Demo 120 Hari", start_date=START_DATE,
            pond_id=pond_id, last_updated=now, is_active=False,
        )
        cycle.save()
        cycle_id = str(cycle.id)
        self.stdout.write(f"Cycle created: {cycle_id}")

        pond.active_cycle_id = cycle_id
        pond.save()

        CycleData(cycle_id=cycle_id, result_data=result_rows, last_updated=now).save()
        ResultData(cycle_id=cycle_id, result_data=result_computed, last_updated=now).save()
        ForecastData(cycle_id=cycle_id, result_data=[], last_updated=now).save()

        for fr in feed_rows:
            FeedRealization(
                cycle_id=cycle_id, doc=fr["doc"], ration_number=fr["ration_number"],
                feed_ration=fr["feed_ration"], feed_given=fr["feed_given"],
                feed_leftover=fr["feed_leftover"], last_updated=now,
            ).save()
        self.stdout.write(f"FeedRealization: {len(feed_rows)} records saved")

        HarvestRecord(cycle_id=cycle_id, harvest_data=harvest_data, last_updated=now).save()
        self.stdout.write("HarvestRecord:   1 record saved")

        CostData(farm_id=cycle_id, data=cost_rows, last_updated=now).save()
        self.stdout.write(f"CostData:        {len(cost_rows)} entries saved")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Add these to your .env file:")
        self.stdout.write("=" * 60)
        self.stdout.write(f"SEEDER_FARM={farm_id}")
        self.stdout.write(f"SEEDER_POND={pond_id}")
        self.stdout.write(f"SEEDER_CYCLE={cycle_id}")
        self.stdout.write("=" * 60)
        self.stdout.write("Done. Every new user who signs in will get this data cloned.")

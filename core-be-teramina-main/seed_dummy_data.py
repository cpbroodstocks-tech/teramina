"""
Seed a demo farm with 80 days of culture data.

Usage (from core-be-teramina-main/):
    .venv/bin/python seed_dummy_data.py [--email user@example.com]
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teramina.settings")
django.setup()

import numpy as np
import pandas as pd

# ── Models ────────────────────────────────────────────────────────────────────
from teramina.water_quality_dashboard.models.variable_model import Variable, WQVariable
from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.user.models.user_model import User
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.feeding.models.feeding_recommendation_model import FeedingRecommendation
from teramina.harvest.models.harvest_record_model import HarvestRecord

# ── Pipeline helpers ───────────────────────────────────────────────────────────
from teramina.data_generator.combined_data_generator import CombinedDataGenerator
from teramina.helpers.database_updater import (
    update_historical_data_result,
    update_forecast_combined_data_result,
    set_last_updated,
)

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic data generation
# ─────────────────────────────────────────────────────────────────────────────

DOC_MAX = 80
POND_SIZE_M2 = 2000
STOCKING_DENSITY = 100          # PL / m²
INITIAL_STOCKING = POND_SIZE_M2 * STOCKING_DENSITY   # 200 000 PL
START_DATE = datetime(2026, 1, 30)   # DOC 1 = 80 days before 2026-04-20

# ABW key-points (g) – realistic L. vannamei growth
_ABW_DOCS = [1,  10,  20,  30,  40,  50,  60,  70,  80]
_ABW_VALS = [0.05, 0.6, 2.5, 5.5, 9.0, 12.5, 15.5, 17.5, 18.5]


def _make_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    docs = np.arange(1, DOC_MAX + 1)

    # ABW with small noise
    abw_base = np.interp(docs, _ABW_DOCS, _ABW_VALS)
    abw = abw_base * (1 + rng.normal(0, 0.02, DOC_MAX))
    abw = np.round(np.clip(abw, 0.01, None), 3)

    # SR – monotone decreasing, ~87 % at DOC 80
    sr = np.clip(1.0 - 0.0016 * docs, 0.80, 1.0)
    sr = np.round(sr, 4)

    # Population / Biomass
    population = np.round(INITIAL_STOCKING * sr).astype(int)
    biomass_kg = population * abw / 1000.0

    # Feeding rate (% biomass) – tapers with age
    fr_rate = np.where(docs <= 15, 0.12,
              np.where(docs <= 30, 0.07,
              np.where(docs <= 50, 0.045, 0.030)))
    feed_given = np.round(np.maximum(biomass_kg * fr_rate, 1.0), 1)

    # Water quality
    temperature = np.round(np.clip(28.5 + rng.normal(0, 0.6, DOC_MAX), 26.0, 32.0), 1)
    do          = np.round(np.clip(6.5  + rng.normal(0, 0.9, DOC_MAX),  3.5,  9.0), 2)
    nh3_base    = 0.02 + 0.002 * docs
    nh3         = np.round(np.clip(nh3_base + np.abs(rng.normal(0, 0.02, DOC_MAX)), 0.001, 0.30), 3)
    ph          = np.round(np.clip(8.0  + rng.normal(0, 0.15, DOC_MAX), 7.0,  8.8), 2)
    alkalinity  = np.round(np.clip(130  + rng.normal(0, 10,   DOC_MAX), 80,   200), 1)
    salinity    = np.round(np.clip(16   + rng.normal(0, 1.5,  DOC_MAX), 10,   25 ), 1)

    # Costs (IDR)
    labor_cost    = np.full(DOC_MAX, 500_000.0)
    energy_cost   = np.round(300_000 + feed_given * 2_000, 0)
    feeding_cost  = np.round(feed_given * 12_000, 0)
    probiotic_cost= np.where(docs <= 30, 150_000.0, 80_000.0)
    other_cost    = np.full(DOC_MAX, 50_000.0)
    bonus_cost    = np.zeros(DOC_MAX)
    harvest_cost  = np.zeros(DOC_MAX)

    # Dates
    dates = [START_DATE + timedelta(days=int(d) - 1) for d in docs]

    # Sampling days: every 7th DOC (DOC 7, 14, 21, … 77)
    # Simulate two trays with ~4 % measurement noise; None on non-sampling days
    sampling_mask = (docs % 7 == 0)
    sampling_tray_1 = [
        round(float(abw_base[i]) * (1 + rng.normal(0, 0.04)), 2) if sampling_mask[i] else None
        for i in range(DOC_MAX)
    ]
    sampling_tray_2 = [
        round(float(abw_base[i]) * (1 + rng.normal(0, 0.04)), 2) if sampling_mask[i] else None
        for i in range(DOC_MAX)
    ]

    df = pd.DataFrame({
        "date":             dates,
        "doc":              docs,
        "abw":              abw,
        "sr":               sr,
        "w0":               abw[0],           # initial ABW – scalar broadcast
        "initial_stocking": float(INITIAL_STOCKING),
        "temperature":      temperature,
        "do":               do,
        "nh3":              nh3,
        "ph":               ph,
        "alkalinity":       alkalinity,
        "salinity":         salinity,
        "feed_given":       feed_given,
        "fr":               None,             # computed downstream
        "protein_content":  36.0,
        "chb":              72.0,
        "labor_cost":       labor_cost,
        "bonus_cost":       bonus_cost,
        "energy_cost":      energy_cost,
        "probiotic_cost":   probiotic_cost,
        "other_cost":       other_cost,
        "harvest_cost":     harvest_cost,
        "feeding_cost":     feeding_cost,
        "sampling_tray_1":  sampling_tray_1,
        "sampling_tray_2":  sampling_tray_2,
    })

    return df, feed_given, population


def _seed_wq_config():
    """Seed the singleton Variable document + WQVariable thresholds if missing."""
    wq_names = [
        "temperature", "do", "nh3", "ph", "alkalinity", "salinity",
        "nh4", "tan", "orp", "ca", "mg", "hardness", "po4", "no2", "no3",
        "plankton", "tss", "turbidity", "conductivity",
    ]
    if not Variable.objects().first():
        Variable(data=wq_names).save()
        print("  Seeded Variable document")

    wq_thresholds = [
        dict(name="temperature", weight=0.15, type="float",
             lower_bound=23, optimal_min=27, optimal_max=30, upper_bound=33),
        dict(name="do",          weight=0.25, type="float",
             lower_bound=2,  optimal_min=3.5, optimal_max=9,  upper_bound=10),
        dict(name="nh3",         weight=0.20, type="float",
             lower_bound=0,  optimal_min=0,   optimal_max=0.25, upper_bound=2.09),
        dict(name="ph",          weight=0.15, type="float",
             lower_bound=6.5, optimal_min=7.5, optimal_max=8.5, upper_bound=9),
        dict(name="alkalinity",  weight=0.10, type="float",
             lower_bound=50, optimal_min=100, optimal_max=200, upper_bound=300),
        dict(name="salinity",    weight=0.10, type="float",
             lower_bound=5,  optimal_min=10,  optimal_max=25,  upper_bound=35),
        dict(name="tss",         weight=0.05, type="float",
             lower_bound=0,  optimal_min=0,   optimal_max=100, upper_bound=300),
    ]
    if not WQVariable.objects().first():
        for t in wq_thresholds:
            WQVariable(**t).save()
        print(f"  Seeded {len(wq_thresholds)} WQVariable thresholds")


def _seed_feeding(cycle_id: str, feed_given: np.ndarray):
    """Seed FeedRealization (4 rations/day) + FeedingRecommendation (1/day)."""
    rng = np.random.default_rng(7)
    splits = [0.30, 0.25, 0.25, 0.20]

    realizations = []
    recommendations = []

    for doc_idx, total_feed in enumerate(feed_given):
        doc = doc_idx + 1
        ration_per_slot = [round(total_feed * s, 2) for s in splits]

        for ration_num, ration_kg in enumerate(ration_per_slot, start=1):
            noise = rng.uniform(0.92, 1.06)
            given = round(ration_kg * noise, 2)
            leftover = round(max(0.0, ration_kg - given + rng.uniform(0, 0.3)), 2)
            realizations.append(FeedRealization(
                cycle_id=cycle_id,
                doc=doc,
                ration_number=ration_num,
                feed_ration=ration_kg,
                feed_given=given,
                feed_leftover=leftover,
            ))

        recommendations.append(FeedingRecommendation(
            cycle_id=cycle_id,
            doc=doc,
            recommended_ration_kg=round(total_feed, 2),
            recommended_frequency=4,
            ration_per_feeding=ration_per_slot,
            adjustment_reason="Rule-based blind feed",
            model_layer="rule_v1",
            model_version="1.0",
            confidence=0.85,
        ))

    FeedRealization.objects(cycle_id=cycle_id).delete()
    FeedingRecommendation.objects(cycle_id=cycle_id).delete()
    FeedRealization.objects.insert(realizations, load_bulk=False)
    FeedingRecommendation.objects.insert(recommendations, load_bulk=False)

    print(f"  Seeded {len(realizations)} feed realizations, {len(recommendations)} recommendations")


def _seed_harvest(cycle_id: str, population: np.ndarray, feed_given: np.ndarray):
    """Seed one partial harvest at DOC 60 (20 % biomass reduction)."""
    doc60_idx = 59   # 0-based
    abw_at60 = np.interp(60, _ABW_DOCS, _ABW_VALS)
    pop_at60 = int(population[doc60_idx])
    partial_pop = int(pop_at60 * 0.20)
    partial_biomass = round(partial_pop * abw_at60 / 1000, 1)

    # ~90 000 IDR/kg for ~size-65 shrimp (15.5 g ABW)
    price_per_kg = 90_000
    partial_revenue = round(partial_biomass * price_per_kg, 0)

    harvest_data = {
        "partial1": {
            "doc": 60,
            "biomass": partial_biomass,
            "revenue": partial_revenue,
        }
    }

    HarvestRecord.objects(cycle_id=cycle_id).delete()
    HarvestRecord(cycle_id=cycle_id, harvest_data=harvest_data).save()
    print(f"  Seeded partial harvest at DOC 60: {partial_biomass} kg, "
          f"revenue IDR {partial_revenue:,.0f}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed 80-day dummy cycle data")
    parser.add_argument("--email", help="Attach farm to this user email")
    args = parser.parse_args()

    # ── Resolve user ──────────────────────────────────────────────────────────
    if args.email:
        user = User.objects(email=args.email).first()
        if not user:
            print(f"ERROR: user '{args.email}' not found in DB")
            sys.exit(1)
    else:
        user = User.objects.first()
        if not user:
            print("ERROR: No users found. Run --email <addr> to specify.")
            sys.exit(1)

    print(f"Seeding data for: {user.email} ({user.id})")

    # ── Global config (idempotent) ─────────────────────────────────────────────
    print("Ensuring WQ config…")
    _seed_wq_config()

    # ── Create Farm ───────────────────────────────────────────────────────────
    farm = Farm(
        name="Demo Farm – Teramina",
        location="Sidoarjo, Jawa Timur",
        user_id=str(user.id),
    )
    farm.save()
    print(f"  Farm:  {farm.name} ({farm.id})")

    # ── Create Pond ───────────────────────────────────────────────────────────
    pond = Pond(
        name="A1",
        size=float(POND_SIZE_M2),
        depth=1.5,
        pond_construction="HDPE",
        pond_shape="Persegi",
        farm_id=str(farm.id),
        is_active=True,
    )
    pond.save()
    print(f"  Pond:  {pond.name} ({pond.id})")

    # ── Create Cycle ──────────────────────────────────────────────────────────
    cycle = Cycle(
        name="Siklus 1 – 2026",
        start_date=START_DATE,
        pond_id=str(pond.id),
        is_active=True,
    )
    cycle.save()
    pond.active_cycle_id = str(cycle.id)
    pond.save()
    print(f"  Cycle: {cycle.name} ({cycle.id})")

    cycle_id = str(cycle.id)

    # ── Generate synthetic DataFrame ──────────────────────────────────────────
    print("\nGenerating 80-day synthetic dataset…")
    df, feed_given, population = _make_df()
    df["cycle_id"] = cycle_id

    # ── Run the full data pipeline (no Pinecone) ──────────────────────────────
    print("Running CombinedDataGenerator…")

    # The price service is an external HTTP API that may be unreachable locally.
    # Patch get_price_array with a static IDR price table (count/kg → IDR/kg).
    # The price service is an external HTTP API that may be unreachable locally.
    # Patch the reference inside the module that actually calls it.
    _FALLBACK_PRICES = np.array([
        [20, 140_000], [30, 120_000], [40, 105_000], [50,  95_000],
        [60,  87_000], [70,  78_000], [80,  70_000], [100, 62_000],
    ], dtype=float)
    import teramina.data_generator.historical.historical_data_generator as _hdg
    import teramina.data_generator.forecast.forecast_data_based_adg as _fdg
    import teramina.data_generator.optimization_data_generator as _odg
    import teramina.data_generator.forecast.forecast_data_generator as _fdg2
    _price_stub = lambda _cycle_id: _FALLBACK_PRICES
    _hdg.get_price_array = _price_stub
    _fdg.get_price_array = _price_stub
    _odg.get_price_array = _price_stub
    _fdg2.get_price_array = _price_stub

    try:
        combined_df = CombinedDataGenerator(cycle_id).generate_data(df)
    except Exception as exc:
        print(f"ERROR in CombinedDataGenerator: {exc}")
        raise

    historical_df = combined_df.query("category == 'historical'").reset_index(drop=True)

    # Save raw input data
    CycleData.objects(cycle_id=cycle_id).update_one(
        set__result_data=df.to_dict("records"),
        upsert=True,
    )

    # Save processed historical results
    update_historical_data_result(cycle_id, historical_df)

    # Save combined forecast data
    if historical_df.shape[0] > 1:
        update_forecast_combined_data_result(cycle_id, combined_df)

    # Propagate last_updated timestamps up the chain
    set_last_updated(cycle_id)

    # Mark user as having data
    User.objects(id=str(user.id)).update(set__is_there_data=True)

    print(f"  Saved {len(historical_df)} historical rows + forecast")

    # ── Seed feeding data ─────────────────────────────────────────────────────
    print("Seeding feeding data…")
    _seed_feeding(cycle_id, feed_given)

    # ── Seed harvest data ─────────────────────────────────────────────────────
    print("Seeding harvest data…")
    _seed_harvest(cycle_id, population, feed_given)

    print(f"""
╔══════════════════════════════════════════════════╗
║  Seed complete                                   ║
╠══════════════════════════════════════════════════╣
║  Farm ID  : {farm.id}
║  Pond ID  : {pond.id}
║  Cycle ID : {cycle.id}
╚══════════════════════════════════════════════════╝
Navigate to the cycle detail page to verify all tabs.
""")


if __name__ == "__main__":
    main()

"""
Management command: fix_energy_cost
------------------------------------
Patches existing ResultData documents where energy_cost was entered as an
IDR/month budget (e.g. 800,000) instead of the per-Wh rate multiplier
(e.g. 12) expected by cost_formula.py:

    cost_energy_per_day = energy_cost × AERATOR_WATTS(820) × HOURS_PER_DAY(24)

Any cycle whose ResultData has average energy_cost > 100 is assumed to be
using the wrong unit and will be corrected.

Usage:
    python manage.py fix_energy_cost            # dry-run (prints what would change)
    python manage.py fix_energy_cost --apply    # write corrections to MongoDB
"""

import numpy as np
import pandas as pd

from django.core.management.base import BaseCommand

from teramina.cycle_data.models.cycle_data_model import ResultData
from teramina.helpers.constant_value import Constant

ENERGY_RATE_CORRECT = 12.0          # IDR/Wh rate that matches real-data examples
ENERGY_THRESHOLD = 100              # energy_cost values above this are treated as monthly IDR

AERATOR = Constant.AERATOR_WATTS    # 820
HOURS = Constant.HOURS_PER_DAY     # 24
CORRECT_DAILY = ENERGY_RATE_CORRECT * AERATOR * HOURS   # ≈ 235,520 IDR/day


class Command(BaseCommand):
    help = "Fix inflated energy_cost values in all ResultData documents"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually write the corrections (default is dry-run)",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(f"Mode: {mode}\n")

        results = ResultData.objects().all()
        total = results.count()
        self.stdout.write(f"Found {total} ResultData documents\n")

        patched = 0
        skipped = 0

        for rd in results:
            if not rd.result_data:
                skipped += 1
                continue

            df = pd.DataFrame(rd.result_data)

            if "energy_cost" not in df.columns or "cost_energy" not in df.columns:
                self.stdout.write(f"  cycle {rd.cycle_id}: missing cost columns, skip")
                skipped += 1
                continue

            avg_energy_cost = df["energy_cost"].mean()
            if avg_energy_cost <= ENERGY_THRESHOLD:
                skipped += 1
                continue

            # --- compute correction ------------------------------------------------
            old_cost_energy = df["cost_energy"].copy()
            new_cost_energy = pd.Series([CORRECT_DAILY] * len(df), dtype=float)
            delta_per_row = old_cost_energy - new_cost_energy  # how much to subtract

            df["energy_cost"] = ENERGY_RATE_CORRECT
            df["cost_energy"] = new_cost_energy

            # total_cost per row
            cost_cols = ["cost_harvest", "cost_energy", "cost_probiotics",
                         "cost_other", "cost_labor", "cost_bonuss", "cost_feed"]
            existing_cost_cols = [c for c in cost_cols if c in df.columns]
            df["total_cost"] = df[existing_cost_cols].sum(axis=1)

            # cumulative fields
            df["cum_total_cost"] = df["total_cost"].cumsum()

            if "cum_realized_revenue" in df.columns:
                df["profit"] = df["cum_realized_revenue"] - df["cum_total_cost"]
            elif "realized_revenue" in df.columns:
                df["profit"] = df["realized_revenue"].cumsum() - df["cum_total_cost"]

            if "total_biomass" in df.columns:
                biomass = df["total_biomass"].replace(0, np.nan)
                df["cost_per_kg"] = (df["cum_total_cost"] / biomass).round(0)

            old_total = old_cost_energy.sum()
            new_total = new_cost_energy.sum()
            self.stdout.write(
                f"  cycle {rd.cycle_id}: avg energy_cost {avg_energy_cost:.0f} → {ENERGY_RATE_CORRECT}  |  "
                f"cum cost_energy {old_total/1e9:.1f}B → {new_total/1e6:.1f}M IDR"
            )

            if apply:
                df = df.where(pd.notnull(df), None)
                df = df.replace({np.nan: None})
                rd.result_data = df.to_dict("records")
                rd.save()

            patched += 1

        self.stdout.write(f"\nPatched: {patched}  |  Skipped: {skipped}")
        if not apply:
            self.stdout.write("Re-run with --apply to write changes.")

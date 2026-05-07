"""
Management command: regen_cycle_data
-------------------------------------
Fixes inflated energy_cost in CycleData (users enter daily IDR budget but the
formula treats it as IDR/Wh and multiplies by AERATOR_WATTS×HOURS_PER_DAY again),
then regenerates ResultData and ForecastData from the corrected CycleData.

Root cause:
    users enter `listrik` column = daily electricity cost in IDR (e.g. 302,400)
    cost_formula: cost_per_day = energy_cost × 820 × 24  (treats stored value as IDR/Wh)
    result: 302,400 × 19,680 ≈ 5.95 billion IDR/day → -680B profit

Fix:
    energy_cost_rate = daily_cost / (AERATOR_WATTS × HOURS_PER_DAY)
    = 302,400 / 19,680 = 15.37 IDR/Wh
    Then: 15.37 × 19,680 = 302,400 IDR/day  ✓

Usage:
    python manage.py regen_cycle_data                    # dry-run, all cycles
    python manage.py regen_cycle_data --cycle_id <id>   # dry-run, one cycle
    python manage.py regen_cycle_data --apply            # apply all
    python manage.py regen_cycle_data --cycle_id <id> --apply
"""

import pandas as pd

from django.core.management.base import BaseCommand

from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.data_generator.combined_data_generator import CombinedDataGenerator
from teramina.helpers.constant_value import Constant
from teramina.helpers.database_updater import (
    update_historical_data_result,
    update_forecast_combined_data_result,
)

ENERGY_THRESHOLD = 100  # energy_cost values above this are treated as daily IDR
RATE_DIVISOR = Constant.AERATOR_WATTS * Constant.HOURS_PER_DAY  # 19,680


class Command(BaseCommand):
    help = "Fix CycleData energy_cost and regenerate ResultData / ForecastData"

    def add_arguments(self, parser):
        parser.add_argument("--cycle_id", type=str)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        apply = options["apply"]
        self.stdout.write(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")

        if options.get("cycle_id"):
            qs = CycleData.objects(cycle_id=options["cycle_id"])
        else:
            qs = CycleData.objects()

        for cd in qs:
            if not cd.result_data:
                continue

            df = pd.DataFrame(cd.result_data)
            if "energy_cost" not in df.columns:
                continue

            avg = df["energy_cost"].mean()
            if pd.isna(avg) or avg <= ENERGY_THRESHOLD:
                self.stdout.write(f"  {cd.cycle_id}: energy_cost={avg:.2f} — OK, skip")
                continue

            # Divide each row individually to preserve day-by-day variation
            corrected_avg = avg / RATE_DIVISOR
            self.stdout.write(
                f"  {cd.cycle_id}: avg energy_cost {avg:.0f} → ~{corrected_avg:.4f} IDR/Wh "
                f"(daily avg={corrected_avg * RATE_DIVISOR:.0f} IDR/day)"
            )

            if apply:
                # 1. Patch CycleData energy_cost column (per-row correction)
                df["energy_cost"] = df["energy_cost"] / RATE_DIVISOR
                cd.result_data = df.to_dict("records")
                cd.save()
                self.stdout.write(f"    CycleData patched")

                # 2. Regenerate ResultData and ForecastData
                try:
                    combined_df = CombinedDataGenerator(cd.cycle_id).generate_data(df)

                    historical_df = combined_df.query(
                        "category == 'historical'"
                    ).reset_index(drop=True)

                    update_historical_data_result(cd.cycle_id, historical_df)

                    if historical_df.shape[0] > 1:
                        update_forecast_combined_data_result(cd.cycle_id, combined_df)

                    self.stdout.write(f"    ResultData + ForecastData regenerated")
                except Exception as exc:  # pylint: disable=broad-except
                    self.stderr.write(f"    ERROR regenerating {cd.cycle_id}: {exc}")

        if not apply:
            self.stdout.write("\nRe-run with --apply to commit.")

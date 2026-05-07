"""
Management command: fix_harvest_record
---------------------------------------
Fixes the seeded HarvestRecord documents that were stored as flat dicts
instead of the canonical nested format expected by harvest_service /
forecast_service:

    {"final": {"doc": int, "biomass": float, "revenue": float},
     "partial1": {"doc": int, "biomass": float, "revenue": float},
     "partial2": {"doc": "", "biomass": "", "revenue": ""},
     "partial3": {"doc": "", "biomass": "", "revenue": ""}}

Usage:
    python manage.py fix_harvest_record --cycle_id <id>   # dry-run
    python manage.py fix_harvest_record --cycle_id <id> --apply
    python manage.py fix_harvest_record --all             # all seed cycles
    python manage.py fix_harvest_record --all --apply
"""

from django.core.management.base import BaseCommand

from teramina.harvest.models.harvest_record_model import HarvestRecord


def is_flat_format(harvest_data):
    """True if this is a flat dict (seeded wrong format) rather than nested."""
    return isinstance(harvest_data, dict) and "final" not in harvest_data


def build_nested(records):
    """Convert a list of flat harvest dicts to the canonical nested format."""
    partials = [r for r in records if r.get("is_partial")]
    finals = [r for r in records if not r.get("is_partial")]

    nested = {
        "partial1": {"doc": "", "biomass": "", "revenue": ""},
        "partial2": {"doc": "", "biomass": "", "revenue": ""},
        "partial3": {"doc": "", "biomass": "", "revenue": ""},
        "final":    {"doc": "", "biomass": "", "revenue": ""},
    }

    for i, ev in enumerate(partials[:3], start=1):
        biomass = ev.get("harvest_biomass_kg", "")
        price = ev.get("price_per_kg_idr", 0)
        nested[f"partial{i}"] = {
            "doc": ev.get("doc", ""),
            "biomass": biomass,
            "revenue": round(biomass * price, 0) if biomass != "" else "",
        }

    if finals:
        ev = finals[0]
        biomass = ev.get("harvest_biomass_kg", "")
        price = ev.get("price_per_kg_idr", 0)
        nested["final"] = {
            "doc": ev.get("doc", ""),
            "biomass": biomass,
            "revenue": round(biomass * price, 0) if biomass != "" else "",
        }

    return nested


class Command(BaseCommand):
    help = "Fix HarvestRecord documents from flat format to nested format"

    def add_arguments(self, parser):
        parser.add_argument("--cycle_id", type=str, help="Specific cycle_id to fix")
        parser.add_argument("--all", action="store_true", help="Fix all cycles")
        parser.add_argument("--apply", action="store_true", help="Actually save changes (default is dry-run)")

    def handle(self, *args, **options):
        apply = options["apply"]
        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(f"Mode: {mode}")

        if options.get("cycle_id"):
            records = list(HarvestRecord.objects(cycle_id=options["cycle_id"]))
        elif options.get("all"):
            records = list(HarvestRecord.objects())
        else:
            self.stderr.write("Provide --cycle_id <id> or --all")
            return

        # Group by cycle_id
        by_cycle = {}
        for r in records:
            by_cycle.setdefault(r.cycle_id, []).append(r)

        fixed = 0
        for cycle_id, cycle_records in by_cycle.items():
            if len(cycle_records) == 1 and not is_flat_format(cycle_records[0].harvest_data):
                # Check if all required keys are present
                data = cycle_records[0].harvest_data
                missing = [k for k in ["final", "partial1", "partial2", "partial3"] if k not in data]
                if not missing:
                    self.stdout.write(f"  {cycle_id}: already nested format — skip")
                    continue
                # Single nested record but missing some keys — fill with empty defaults
                self.stdout.write(f"  {cycle_id}: missing keys {missing} — filling with empty defaults")
                if apply:
                    for k in missing:
                        data[k] = {"doc": "", "biomass": "", "revenue": ""}
                    cycle_records[0].harvest_data = data
                    cycle_records[0].save()
                    self.stdout.write(f"    → Saved")
                fixed += 1
                continue

            if len(cycle_records) == 1 and is_flat_format(cycle_records[0].harvest_data):
                # Single record but flat — shouldn't happen with our seed but handle it
                self.stdout.write(f"  {cycle_id}: single flat record — skip (manual review needed)")
                continue

            # Multiple records per cycle — the wrong seeded format
            flat_dicts = [r.harvest_data for r in cycle_records]
            nested = build_nested(flat_dicts)
            self.stdout.write(f"  {cycle_id}: {len(cycle_records)} flat records → 1 nested")
            self.stdout.write(f"    final: doc={nested['final']['doc']}, biomass={nested['final']['biomass']}")
            self.stdout.write(f"    partial1: doc={nested['partial1']['doc']}, biomass={nested['partial1']['biomass']}")

            if apply:
                # Delete all existing records for this cycle
                for r in cycle_records:
                    r.delete()
                # Save single nested record
                HarvestRecord(cycle_id=cycle_id, harvest_data=nested).save()
                self.stdout.write(f"    → Saved")
            fixed += 1

        self.stdout.write(f"\n{fixed} cycle(s) {'fixed' if apply else 'would be fixed'}")
        if not apply:
            self.stdout.write("Re-run with --apply to commit changes.")

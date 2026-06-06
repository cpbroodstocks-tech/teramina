"""Give the configured onboarding seed to users without dashboard-ready data."""

from django.core.management.base import BaseCommand

from teramina.helpers.default_data_updater import ensure_default_data_for_user
from teramina.user.models.user_model import User


class Command(BaseCommand):
    help = "Backfill the default onboarding cycle for users without dashboard-ready data"

    def handle(self, *args, **options):
        seeded = skipped = failed = 0

        for user in User.objects.only("id", "email"):
            try:
                if ensure_default_data_for_user(str(user.id)):
                    seeded += 1
                    self.stdout.write(f"Seeded {user.email}")
                else:
                    skipped += 1
            except Exception as exc:  # pylint: disable=broad-except
                failed += 1
                self.stderr.write(f"Failed {user.email}: {exc}")

        self.stdout.write(f"Onboarding backfill complete: seeded={seeded} skipped={skipped} failed={failed}")
        if failed:
            raise RuntimeError(f"Onboarding backfill failed for {failed} user(s)")

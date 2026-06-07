"""Destructively reset user-owned staging data before reseeding the demo bundle."""

from mongoengine.connection import get_db
from django.core.management.base import BaseCommand, CommandError

from teramina.user.models.user_model import User
from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle


CONFIRMATION = "RESET-STAGING"


class Command(BaseCommand):
    help = "Delete staging application users and user-owned data. Firebase identities are not affected."

    def add_arguments(self, parser):
        parser.add_argument("--environment", required=True)
        parser.add_argument("--confirm", required=True)

    def handle(self, *args, **options):
        if options["environment"] != "staging":
            raise CommandError("reset_staging_demo only runs with --environment staging")
        if options["confirm"] != CONFIRMATION:
            raise CommandError(f"reset_staging_demo requires --confirm {CONFIRMATION}")

        users = list(User.objects.only("id"))
        user_ids = [str(user.id) for user in users]
        if not user_ids:
            self.stdout.write("No staging application users to reset.")
            return

        farm_ids = [str(farm.id) for farm in Farm.objects(user_id__in=user_ids).only("id")]
        pond_ids = [str(pond.id) for pond in Pond.objects(farm_id__in=farm_ids).only("id")]
        cycle_ids = [str(cycle.id) for cycle in Cycle.objects(pond_id__in=pond_ids).only("id")]
        db = get_db()
        deleted = 0
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            result = collection.delete_many(
                {
                    "$or": [
                        {"user_id": {"$in": user_ids}},
                        {"owner_id": {"$in": user_ids}},
                        {"created_by": {"$in": user_ids}},
                        {"reviewer_id": {"$in": user_ids}},
                        {"farm_id": {"$in": farm_ids + cycle_ids}},
                        {"pond_id": {"$in": pond_ids}},
                        {"cycle_id": {"$in": cycle_ids}},
                    ]
                }
            )
            deleted += result.deleted_count

        User.objects(id__in=user_ids).delete()
        self.stdout.write(self.style.SUCCESS(
            f"Staging reset complete: users={len(user_ids)} user_owned_records={deleted}. "
            "Firebase users will recreate application profiles on next login."
        ))

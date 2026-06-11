# pylint: disable=no-member

from datetime import datetime
from bson import ObjectId
from mongoengine.errors import FieldDoesNotExist

from ..models.farm_model import Farm
from ...pond.models.pond_model import Pond
from ...user.models.user_model import User
from ...pond.services.pond_service import PondService

from ..schemas.farm_schema import FarmDataSchema

from ...schemas.general_schema import (
    DataErrorSchema,
    DataSuccessSchema,
    GetListSuccessSchema,
)

from ...helpers.shrimp_price import update_price_table
from ...dashboard.services.readiness import is_dashboard_ready_cycle
from ...cycle.models.cycle_model import Cycle


class FarmService:
    """Farm Services"""

    @staticmethod
    def add_farm(user_id, data: FarmDataSchema):
        """Add farm function"""
        try:
            farm = Farm(name=data.name, location=data.location, user_id=str(user_id))
            farm.save()

            update_price_table(data.location)
        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Farm successfully added",
            payload={
                "id": str(farm.id),
                "name": farm.name,
                "location": farm.location,
                "user_id": farm.user_id,
            },
        )

    @staticmethod
    def update_farm(farm_id, data: FarmDataSchema):
        """Update farm function"""
        try:
            Farm.objects(id=farm_id).update(
                set__name=data.name,
                set__location=data.location,
                set__last_updated=datetime.now(),
            )
            update_price_table(data.location)
        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Farm successfully updated",
            payload={"id": farm_id, "name": data.name, "location": data.location},
        )

    @staticmethod
    def delete_farm(farm_id, user_id):
        """Delete farm function"""
        try:
            for pond in Pond.objects(farm_id=farm_id).only("id").all():
                PondService.delete_pond(pond_id=str(pond.id), user_id=user_id)

            farm_object = Farm.objects(id=farm_id)
            farm_name = farm_object.first().name
            user_id = farm_object.first().user_id
            farm_object.delete()

            if not Farm.objects(user_id=user_id).first():
                User.objects(id=user_id).update(is_there_data=False)

        except (FieldDoesNotExist, AttributeError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Farm {farm_name} with id {farm_id} successfully deleted",
            payload={"id": farm_id},
        )

    @staticmethod
    def archive_farm(farm_id, user_id):
        archived_at = datetime.now()
        pond_ids = [str(pond.id) for pond in Pond.objects(farm_id=farm_id).only("id").all()]
        cycle_ids = [str(cycle.id) for cycle in Cycle.objects(pond_id__in=pond_ids).only("id").all()] if pond_ids else []
        Farm.objects(id=farm_id).update(set__archived_at=archived_at, set__archived_by=str(user_id))
        if pond_ids:
            Pond.objects(id__in=pond_ids).update(
                set__archived_at=archived_at,
                set__archived_by=str(user_id),
                set__active_cycle_id="",
            )
        if cycle_ids:
            Cycle.objects(id__in=cycle_ids).update(set__archived_at=archived_at, set__archived_by=str(user_id))
        return 200, DataSuccessSchema(code=200, message="Farm archived", payload={"id": farm_id})

    @staticmethod
    def restore_farm(farm_id):
        pond_ids = [str(pond.id) for pond in Pond.objects(farm_id=farm_id).only("id").all()]
        cycle_ids = [str(cycle.id) for cycle in Cycle.objects(pond_id__in=pond_ids).only("id").all()] if pond_ids else []
        Farm.objects(id=farm_id).update(unset__archived_at=1, set__archived_by="")
        if pond_ids:
            Pond.objects(id__in=pond_ids).update(unset__archived_at=1, set__archived_by="")
        if cycle_ids:
            Cycle.objects(id__in=cycle_ids).update(unset__archived_at=1, set__archived_by="")
        for pond_id in pond_ids:
            replacement = Cycle.objects(pond_id=pond_id, archived_at=None).order_by("-start_date").only("id").first()
            Pond.objects(id=pond_id).update(set__active_cycle_id=str(replacement.id) if replacement else "")
        return 200, DataSuccessSchema(code=200, message="Farm restored", payload={"id": farm_id})

    def get_hierarchy(self, user_id, include_archived=False):
        farm_query = Farm.objects(user_id=str(user_id))
        if not include_archived:
            farm_query = farm_query(archived_at=None)
        farms = list(farm_query.order_by("name").all())
        farm_ids = [str(farm.id) for farm in farms]

        pond_query = Pond.objects(farm_id__in=farm_ids) if farm_ids else []
        if farm_ids and not include_archived:
            pond_query = pond_query(archived_at=None)
        ponds = list(pond_query.order_by("name").all()) if farm_ids else []
        pond_ids = [str(pond.id) for pond in ponds]

        cycle_query = Cycle.objects(pond_id__in=pond_ids) if pond_ids else []
        if pond_ids and not include_archived:
            cycle_query = cycle_query(archived_at=None)
        cycles = list(cycle_query.order_by("-start_date").all()) if pond_ids else []

        cycles_by_pond = {}
        for cycle in cycles:
            cycles_by_pond.setdefault(cycle.pond_id, []).append({
                "id": str(cycle.id),
                "name": cycle.name,
                "pond_id": cycle.pond_id,
                "start_date": cycle.start_date,
                "is_active": cycle.is_active,
                "is_archived": cycle.archived_at is not None,
                "dashboard_ready": is_dashboard_ready_cycle(str(cycle.id)),
                "demo_scenario": cycle.demo_scenario,
            })

        ponds_by_farm = {}
        for pond in ponds:
            pond_cycles = cycles_by_pond.get(str(pond.id), [])
            ponds_by_farm.setdefault(pond.farm_id, []).append({
                "id": str(pond.id),
                "name": pond.name,
                "farm_id": pond.farm_id,
                "size": pond.size,
                "pond_construction": pond.pond_construction,
                "pond_shape": pond.pond_shape,
                "is_active": pond.is_active,
                "is_archived": pond.archived_at is not None,
                "active_cycle_id": pond.active_cycle_id or "",
                "demo_scenario": pond.demo_scenario,
                "cycles": pond_cycles,
            })

        payload = {
            "farms": [{
                "id": str(farm.id),
                "name": farm.name,
                "location": farm.location,
                "is_archived": farm.archived_at is not None,
                "demo_bundle_version": farm.demo_bundle_version,
                "is_demo": bool(farm.demo_bundle_version),
                "ponds": ponds_by_farm.get(str(farm.id), []),
            } for farm in farms]
        }
        return 200, DataSuccessSchema(code=200, message="Hierarchy loaded", payload=payload)

    def get_all_farm(self, user_id, page: int = 1, limit: int = 50):
        """get all farm data"""
        try:
            limit = min(limit, 100)
            offset = (page - 1) * limit
            farm = Farm.objects(user_id=str(user_id), archived_at=None).skip(offset).limit(limit).all()
            farm = [i.to_mongo().to_dict() for i in farm]

            # Collect all farm IDs and stringify ObjectId in one pass
            farm_ids = []
            for i in farm:
                if isinstance(i["_id"], ObjectId):
                    i["_id"] = str(i["_id"])
                farm_ids.append(i["_id"])

            # Batch-load all ponds for all farms in a single query (avoids N+1)
            pond_info_map = self.__get_pond_info_batch(farm_ids)
            for i in farm:
                i.update(pond_info_map.get(i["_id"], {"total_pond": 0, "active_pond": 0, "inactive_pond": 0}))

        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, GetListSuccessSchema(
            code=200, message="Farm data successfully loaded", payload=farm
        )

    def __get_pond_info_batch(self, farm_ids):
        """Fetch pond counts for all farm_ids in a single query."""
        ponds = Pond.objects(farm_id__in=farm_ids, archived_at=None).only("farm_id", "is_active").all()

        pond_info_map = {fid: {"total_pond": 0, "active_pond": 0, "inactive_pond": 0} for fid in farm_ids}
        for pond in ponds:
            info = pond_info_map.get(pond.farm_id)
            if info is None:
                continue
            info["total_pond"] += 1
            if pond.is_active:
                info["active_pond"] += 1
            else:
                info["inactive_pond"] += 1

        return pond_info_map

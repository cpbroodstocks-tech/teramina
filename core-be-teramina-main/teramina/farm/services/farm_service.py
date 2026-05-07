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
            pond = Pond.objects(farm_id=farm_id).first()
            if pond:
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

    def get_all_farm(self, user_id, page: int = 1, limit: int = 50):
        """get all farm data"""
        try:
            limit = min(limit, 100)
            offset = (page - 1) * limit
            farm = Farm.objects(user_id=str(user_id)).skip(offset).limit(limit).all()
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
        ponds = Pond.objects(farm_id__in=farm_ids).only("farm_id", "is_active").all()

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

# pylint: disable=no-member,E0401

from datetime import datetime
from mongoengine.errors import FieldDoesNotExist, InvalidQueryError

from teramina.pond.models.pond_model import Pond
from teramina.farm.models.farm_model import Farm
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle.services.cycle_service import CycleService

from teramina.pond.schemas.pond_schema import PondDataSchema, UpdatePondSchema
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema


class PondService:
    """Pond Services: Manage data pond data in a farm"""

    @staticmethod
    def add_pond(farm_id, data: PondDataSchema):
        """add a new pond"""
        try:
            pond = Pond(
                name=data.name,
                size=data.size,
                pond_construction=data.pond_construction,
                pond_shape=data.pond_shape,
                farm_id=str(farm_id),
            )
            pond.save()
        except FieldDoesNotExist:
            return 400, DataErrorSchema(code=400, message="Failed to add pond data")

        return 200, DataSuccessSchema(
            code=200,
            message="Pond successfully added",
            payload={
                "id": str(pond.id),
                "name": pond.name,
                "size": pond.size,
                "pond_construction": pond.pond_construction,
                "pond_shape": pond.pond_shape,
                "farm_id": pond.farm_id,
                "is_active": pond.is_active,
            },
        )

    @staticmethod
    def get_pond(farm_id, page: int = 1, limit: int = 100):
        """get list pond in a farm"""
        try:
            limit = min(limit, 100)
            offset = (page - 1) * limit
            pond = Pond.objects(farm_id=farm_id).skip(offset).limit(limit).all()
            pond = [i.to_mongo().to_dict() for i in pond]

            for i in pond:
                i["_id"] = str(i["_id"])

            farm = Farm.objects(id=farm_id).first()

        except InvalidQueryError:
            return 400, DataErrorSchema(code=400, message="Failed to get pond data")

        return 200, DataSuccessSchema(
            code=200,
            message="Get Pond successfull",
            payload={"farm_name": farm.name, "farm_id": farm_id, "data": pond},
        )

    @staticmethod
    def update_pond(pond_id, data: UpdatePondSchema):
        """update a pond"""
        try:
            pond = Pond.objects(id=pond_id).first()
            pond.name = data.name
            pond.size = data.size
            pond.pond_construction = data.pond_construction
            pond.pond_shape = data.pond_shape
            pond.last_updated = datetime.now()
            pond.is_active = data.is_active

            pond.save()

        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Pond successfully updated",
            payload={
                "id": str(pond.id),
                "name": pond.name,
                "size": pond.size,
                "pond_construction": pond.pond_construction,
                "pond_shape": pond.pond_shape,
                "farm_id": pond.farm_id,
                "is_active": pond.is_active,
            },
        )

    @staticmethod
    def delete_pond(pond_id, user_id):
        """delete a pond"""
        try:
            cycle = Cycle.objects(pond_id=pond_id).first()

            if cycle:
                CycleService().delete_cycle(str(cycle.id), user_id)

            pond_object = Pond.objects(id=pond_id)
            pond_name = pond_object.first().name
            pond_object.delete()

        except (FieldDoesNotExist, AttributeError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Pond {pond_name} with id {pond_id} deleted",
            payload={"id": pond_id, "name": pond_name},
        )

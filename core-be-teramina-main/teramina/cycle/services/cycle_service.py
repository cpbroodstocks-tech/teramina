# pylint: disable=no-member

from datetime import datetime
from bson import ObjectId

from mongoengine.errors import FieldDoesNotExist, InvalidQueryError

from teramina.cycle.models.cycle_model import Cycle
from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle_data.models.cycle_data_model import (
    CycleData,
    ResultData,
    ForecastData,
)
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.harvest.models.harvest_record_model import HarvestRecord

from teramina.cycle.schemas.cycle_schema import CreateCycleSchema, UpdateCycleSchema
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from teramina.helpers.pinecone_data_indexing import PineconeIndexing


class CycleService:
    """Cycle service that leads to CRUD operations"""

    def __delete_dependent_data(self, cycle_id):
        for cls in [
            CycleData,
            ResultData,
            HarvestRecord,
            HarvestRecommendation,
            FeedRealization,
            ForecastData,
        ]:
            data = cls.objects(cycle_id=cycle_id).first()
            if data:
                cls.objects(cycle_id=cycle_id).delete()

    def __set_active_cycle_in_pond(self, pond_id):
        cycle = Cycle.objects(pond_id=pond_id).only("id").first()
        Pond.objects(id=pond_id).update(set__active_cycle_id=str(cycle.id))

    def create_cycle(self, pond_id, data: CreateCycleSchema):
        """create/add a new cycle"""
        try:
            start_date = datetime.strptime(data.start_date, "%m/%d/%Y")
            cycle = Cycle(
                name=data.name,
                start_date=start_date,
                pond_id=str(pond_id),
                last_updated=datetime.now(),
            )
            cycle.save()

            self.__set_active_cycle_in_pond(pond_id)

        except ValueError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Cycle successfully added",
            payload={
                "id": str(cycle.id),
                "name": cycle.name,
                "start_date": str(cycle.start_date),
            },
        )

    def get_cycles(self, pond_id, page: int = 1, limit: int = 50):
        """get list of all cycles"""
        try:
            limit = min(limit, 100)
            offset = (page - 1) * limit
            cycles = Cycle.objects(pond_id=str(pond_id)).skip(offset).limit(limit).all()
            cycles = [i.to_mongo().to_dict() for i in cycles]
            for i in cycles:
                if isinstance(i["_id"], ObjectId):
                    i["_id"] = str(i["_id"])

            pond = Pond.objects(id=str(pond_id)).first()
            farm = Farm.objects(id=str(pond.farm_id)).first()

        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Load data success",
            payload={"farm_name": farm.name, "pond_name": pond.name, "data": cycles},
        )

    def update_cycle(self, cycle_id, data: UpdateCycleSchema):
        """update data of a cycle"""
        try:
            cycle = Cycle.objects(id=cycle_id).first()

            start_date = datetime.strptime(data.start_date, "%m/%d/%Y")

            cycle.name = data.name
            cycle.start_date = start_date
            cycle.is_active = data.is_active
            cycle.last_updated = datetime.now()

            cycle.save()
        except ValueError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Cycle {cycle.name} successfully updated",
            payload={
                "id": str(cycle_id),
                "name": cycle.name,
                "start_date": cycle.start_date,
                "last_updated": cycle.last_updated,
                "is_active": cycle.is_active,
            },
        )

    def delete_cycle(self, cycle_id, user_id):
        """delete a cycle"""
        try:
            self.__delete_dependent_data(cycle_id)
            cycle = Cycle.objects(id=cycle_id).first()
            try:
                PineconeIndexing(str(user_id)).delete_index(cycle.vector_list)
                cycle.delete()
            except FieldDoesNotExist:
                cycle.delete()

        except AttributeError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Cycle {cycle.name} successfully deleted",
            payload={"id": str(cycle_id), "name": cycle.name},
        )

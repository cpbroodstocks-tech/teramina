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
from teramina.feeding.models.feeding_recommendation_model import FeedingOverride, FeedingRecommendation
from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.harvest.models.harvest_scenario_model import HarvestScenario
from teramina.cycle_data.models.cycle_model_params_model import CycleModelParams
from teramina.cycle_data.models.upload_log_model import DataUploadLog
from teramina.google_sheets.models.sheet_integration_model import SheetIntegration
from teramina.google_sheets.models.sync_log_model import SheetSyncLog
from teramina.pl_report.models.share_token_model import PLReportShareToken
from teramina.summarize.models.insight_model import CycleInsightCache
from teramina.benchmark.models.benchmark_model import CompletedCycleMetrics

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
            FeedingRecommendation,
            FeedingOverride,
            HarvestScenario,
            CycleModelParams,
            DataUploadLog,
            SheetIntegration,
            SheetSyncLog,
            PLReportShareToken,
            CycleInsightCache,
            CompletedCycleMetrics,
        ]:
            data = cls.objects(cycle_id=cycle_id).first()
            if data:
                cls.objects(cycle_id=cycle_id).delete()

    @staticmethod
    def repair_active_cycle(pond_id):
        pond = Pond.objects(id=pond_id).only("active_cycle_id").first()
        if not pond:
            return
        active = Cycle.objects(id=pond.active_cycle_id, pond_id=pond_id, archived_at=None).only("id").first()
        if active:
            return
        replacement = Cycle.objects(pond_id=pond_id, archived_at=None).order_by("-start_date").only("id").first()
        Pond.objects(id=pond_id).update(set__active_cycle_id=str(replacement.id) if replacement else "")

    def create_cycle(self, pond_id, data: CreateCycleSchema):
        """create/add a new cycle"""
        try:
            if not Pond.objects(id=pond_id, archived_at=None).only("id").first():
                return 400, DataErrorSchema(code=400, message="Cannot add a cycle to an archived pond")
            start_date = datetime.strptime(data.start_date, "%m/%d/%Y")
            cycle = Cycle(
                name=data.name,
                start_date=start_date,
                pond_id=str(pond_id),
                last_updated=datetime.now(),
            )
            cycle.save()

            Pond.objects(id=pond_id, archived_at=None).update(set__active_cycle_id=str(cycle.id))

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
            cycles = Cycle.objects(pond_id=str(pond_id), archived_at=None).skip(offset).limit(limit).all()
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
            payload={
                "farm_id": str(farm.id),
                "farm_name": farm.name,
                "pond_id": str(pond.id),
                "pond_name": pond.name,
                "active_cycle_id": pond.active_cycle_id or "",
                "data": cycles,
            },
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
            pond_id = cycle.pond_id
            try:
                PineconeIndexing(str(user_id)).delete_index(cycle.vector_list)
                cycle.delete()
            except FieldDoesNotExist:
                cycle.delete()
            self.repair_active_cycle(pond_id)

        except AttributeError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Cycle {cycle.name} successfully deleted",
            payload={"id": str(cycle_id), "name": cycle.name},
        )

    def archive_cycle(self, cycle_id, user_id):
        cycle = Cycle.objects(id=cycle_id).first()
        cycle.update(set__archived_at=datetime.now(), set__archived_by=str(user_id))
        self.repair_active_cycle(cycle.pond_id)
        return 200, DataSuccessSchema(code=200, message="Cycle archived", payload={"id": cycle_id})

    def restore_cycle(self, cycle_id):
        cycle = Cycle.objects(id=cycle_id).first()
        if not cycle or not Pond.objects(id=cycle.pond_id, archived_at=None).only("id").first():
            return 400, DataErrorSchema(code=400, message="Restore the parent pond first")
        cycle.update(unset__archived_at=1, set__archived_by="")
        self.repair_active_cycle(cycle.pond_id)
        return 200, DataSuccessSchema(code=200, message="Cycle restored", payload={"id": cycle_id})

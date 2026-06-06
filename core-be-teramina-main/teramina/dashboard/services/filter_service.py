# pylint: disable=E0401
from datetime import date, datetime, timedelta
from mongoengine.errors import InvalidQueryError, ValidationError, DoesNotExist

from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.water_quality_dashboard.services.variable_management import (
    VariableManagement,
)
from teramina.dashboard.services.readiness import is_dashboard_ready_cycle

from teramina.schemas.general_schema import DataErrorSchema, GetListSuccessSchema


def _as_datetime(value):
    """Normalize MongoDB and Google Sheets date values for dashboard filters."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    text = str(value).strip()
    for parser in (
        lambda: datetime.fromisoformat(text.replace("Z", "+00:00")),
        lambda: datetime.strptime(text, "%m/%d/%Y"),
    ):
        try:
            return parser().replace(tzinfo=None)
        except ValueError:
            continue
    raise ValueError(f"Invalid cycle data date: {value}")


class FilterData:
    """Filter service for farm, pond, and cycle data"""

    def __init__(self, user_id) -> None:
        self.user_id = user_id

    @staticmethod
    def _ready_cycles(pond_ids):
        cycles = Cycle.objects(pond_id__in=pond_ids).only("id", "name", "start_date").all()
        return [cycle for cycle in cycles if is_dashboard_ready_cycle(str(cycle.id))]

    def get_list_data_main(self, farm_id=None, pond_id=None, dashboard_ready=False):
        """Get the farm, pond, or cycle options available to the signed-in user."""
        if not farm_id and not pond_id:
            farms = Farm.objects(user_id=self.user_id).only("id", "name").all()
            if not dashboard_ready:
                return farms
            data = []
            for farm in farms:
                pond_ids = [str(pond.id) for pond in Pond.objects(farm_id=str(farm.id)).only("id")]
                if pond_ids and self._ready_cycles(pond_ids):
                    data.append(farm)
        elif farm_id and not pond_id:
            if not Farm.objects(id=farm_id, user_id=self.user_id).only("id").first():
                return []
            ponds = Pond.objects(farm_id=farm_id).only("id", "name").all()
            if not dashboard_ready:
                return ponds
            data = [
                pond
                for pond in ponds
                if self._ready_cycles([str(pond.id)])
            ]
        elif not farm_id and pond_id:
            raise ValueError("farm_id should be not None, if pond_id is not None")
        else:
            if not Farm.objects(id=farm_id, user_id=self.user_id).only("id").first():
                return []
            if not Pond.objects(id=pond_id, farm_id=farm_id).only("id").first():
                return []
            if dashboard_ready:
                data = self._ready_cycles([pond_id])
            else:
                data = Cycle.objects(pond_id=pond_id).only("id", "name", "start_date").all()
        return data

    def get_list_data(self, farm_id=None, pond_id=None, cycle_id=None):
        """get list of data"""
        try:
            if not cycle_id:
                data = self.get_list_data_main(farm_id, pond_id, dashboard_ready=True)
            else:
                if not farm_id or not pond_id:
                    raise ValueError("farm_id and pond_id are required when cycle_id is provided")
                if not Farm.objects(id=farm_id, user_id=self.user_id).only("id").first():
                    raise ValueError("Farm does not exist")
                if not Pond.objects(id=pond_id, farm_id=farm_id).only("id").first():
                    raise ValueError("Pond does not exist")
                data = Cycle.objects(id=cycle_id, pond_id=pond_id).only("id", "name", "start_date").all()
                if not data or not is_dashboard_ready_cycle(cycle_id):
                    raise ValueError(f"Dashboard data with cycle {cycle_id} doesn't exist")

        except DoesNotExist as exc:
            raise DoesNotExist("Some required data do not exist") from exc

        return data

    def check_final_status(self, cycle_id):
        """check the final harvest status"""
        harvest = HarvestRecord.objects(cycle_id=cycle_id).only("harvest_data").first()
        if not harvest:
            return False

        harvest_data = harvest.harvest_data
        if harvest_data["final"]["doc"] != "":
            return harvest_data["final"]["doc"]

        return False

    def filter(
        self,
        farm_id=None,
        pond_id=None,
        cycle_id=None,
        filter_type="historical",
    ):
        """get filtered data"""
        try:
            data = self.get_list_data(farm_id, pond_id, cycle_id)
            result_data = [{"id": str(i.id), "name": i.name} for i in data]
            if cycle_id:
                start_date = datetime.strftime(data[0].start_date, "%m/%d/%Y")
                cycle_data = (
                    CycleData.objects(cycle_id=cycle_id).only("result_data").first()
                )
                if not cycle_data:
                    raise ValueError(f"Data with cycle {cycle_id} doesn't exist")

                if filter_type == "historical":
                    end_date = _as_datetime(cycle_data["result_data"][-1]["date"])
                    end_date = end_date.strftime("%m/%d/%Y")
                else:
                    harvest_recommendation = (
                        HarvestRecommendation.objects(cycle_id=cycle_id)
                        .only("harvest_data")
                        .first()
                    )
                    referenced_doc = (
                        [
                            i[1]["doc"]
                            for i in harvest_recommendation.harvest_data.items()
                        ]
                        if harvest_recommendation
                        else []
                    )
                    start_date = _as_datetime(cycle_data["result_data"][-1]["date"]) + timedelta(
                        days=1
                    )
                    if referenced_doc:
                        end_date = data[0].start_date + timedelta(
                            days=referenced_doc[-1] - 1
                        )
                    else:
                        end_date = start_date + timedelta(
                            days=120 - (cycle_data["result_data"][-1]["doc"] + 1)
                        )

                    start_date = start_date.strftime("%m/%d/%Y")
                    end_date = end_date.strftime("%m/%d/%Y")

                result_data[0]["daterange"] = {
                    "start_date": start_date,
                    "end_date": end_date,
                }

        except (
            InvalidQueryError,
            ValidationError,
            ValueError,
            DoesNotExist,
        ) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, GetListSuccessSchema(
            code=200, message="Get data filter Success", payload=result_data
        )

    def get_start_date(self, cycles: list):
        """get start date"""

        start_date = 0
        for cycle_id in cycles:
            if start_date == 0:
                start_date = (
                    Cycle.objects(id=cycle_id).only("start_date").first().start_date
                )
            else:
                new_start_date = (
                    Cycle.objects(id=cycle_id).only("start_date").first().start_date
                )
                if (start_date - new_start_date).days > 0:
                    start_date = new_start_date

        return start_date

    def get_end_date(self, cycles: list):
        """get end date"""

        end_date = 0
        for cycle_id in cycles:
            cycle_data = (
                CycleData.objects(cycle_id=cycle_id).only("result_data").first()
            )
            if not cycle_data:
                break

            if end_date == 0:
                end_date = _as_datetime(cycle_data["result_data"][-1]["date"])
            else:
                new_end_date = _as_datetime(cycle_data["result_data"][-1]["date"])
                if (new_end_date - end_date).days > 0:
                    end_date = new_end_date

        return end_date

    def get_current_variable(self, cycles: list):
        """get current variable"""
        var_list = []
        for cycle_id in cycles:
            cycle_data = (
                CycleData.objects(cycle_id=cycle_id).only("result_data").first()
            )

            if not cycle_data:
                break
            var_list = list(set(var_list).union(cycle_data["result_data"][-1].keys()))

        return var_list

    def mapping_wq_variables(self, data: list):
        """mapping wq variables"""
        wq_vars = VariableManagement().get_variable_names()
        var_list = [i for i in data if i in wq_vars] + ["wqi_1", "wqi_2"]
        return var_list

    def wq_filter(
        self,
        farm_id: str = None,
        pond_id: str = None,
        cycle_id: str = None,
    ):
        """water quality data"""
        try:
            if not cycle_id:
                data = self.get_list_data_main(farm_id, pond_id)
                result_data = [{"id": str(i.id), "name": i.name} for i in data]
            else:
                cycles = cycle_id.split(",")
                start_date = datetime.strftime(self.get_start_date(cycles), "%Y-%m-%d")
                end_date = datetime.strftime(self.get_end_date(cycles), "%Y-%m-%d")
                variables = self.get_current_variable(cycles)
                variables = self.mapping_wq_variables(variables)
                result_data = [
                    {
                        "data": {
                            "start_date": start_date,
                            "end_date": end_date,
                            "variables": variables,
                        }
                    }
                ]
        except (
            InvalidQueryError,
            ValidationError,
            ValueError,
            DoesNotExist,
        ) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, GetListSuccessSchema(
            code=200, message="Get data filter Success", payload=result_data
        )

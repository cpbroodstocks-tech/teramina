# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..schemas.harvest_scenario_schema import RunSimulationSchema, SaveScenarioSchema
from ..services.harvest_scenario_service import HarvestScenarioService

router = Router(tags=["Harvest Scenarios"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/simulate", response=response_schema, auth=AuthBearer())
def run_simulation(request, cycle_id: str, data: RunSimulationSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestScenarioService.run_simulation(cycle_id, str(user.id), data)


@router.get("/simulate/presets", response=response_schema, auth=AuthBearer())
def get_presets(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestScenarioService.get_presets(cycle_id, str(user.id))


@router.post("/simulate/save", response=response_schema, auth=AuthBearer())
def save_scenario(request, cycle_id: str, data: SaveScenarioSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestScenarioService.save_scenario(cycle_id, str(user.id), data)


@router.get("/simulate/saved", response=response_schema, auth=AuthBearer())
def list_scenarios(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestScenarioService.list_scenarios(cycle_id)

# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner

from ..schemas.harvest_schema import HarvestDataSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..services.harvest_service import HarvestService

router = Router(tags=["Harvest"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/add-harvest-record", response=response_schema, auth=AuthBearer())
def add_harvest_record(request, cycle_id, data: HarvestDataSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestService(cycle_id).add_harvest_record(data)


@router.delete("/delete-harvest-record", response=response_schema, auth=AuthBearer())
def delete_harvest_record(request, cycle_id):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestService(cycle_id).delete_harvest_record()


@router.get("/harvest-record-data", response=response_schema, auth=AuthBearer())
def list_harvest_record(request, cycle_id):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestService(cycle_id).get_harvest_record()


@router.get("/harvest-recommendation", response=response_schema, auth=AuthBearer())
def list_harvest_recommendation(request, cycle_id):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestService(cycle_id).get_harvest_recommendation()


@router.post("/create-harvest-simulation", response=response_schema, auth=AuthBearer())
def create_harvest_simulation(request, cycle_id, data: HarvestDataSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return HarvestService(cycle_id).add_harvest_simulation(data)

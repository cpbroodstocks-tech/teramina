# pylint: disable=missing-function-docstring, unused-argument

from ninja import Body, Router

from teramina.authentication.auth_bearer import AuthBearer
from ..schemas.cycle_schema import CreateCycleSchema, UpdateCycleSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema
from ..services.cycle_service import CycleService
from ...authentication.services.authentication_service import get_signed_in_user
from ...helpers.ownership import verify_pond_owner, verify_cycle_owner

router = Router(tags=["Cycle"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.post("/add-cycle", response=response_schema, auth=AuthBearer())
def add_cycle(request, pond_id, data: CreateCycleSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_pond_owner(pond_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return CycleService().create_cycle(pond_id, data)


@router.get("/list-cycles", response=response_schema, auth=AuthBearer())
def get_cycles(request, pond_id, page: int = 1, limit: int = 50):
    user = get_signed_in_user(request)
    if not verify_pond_owner(pond_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return CycleService().get_cycles(pond_id, page=page, limit=limit)


@router.put("/update-cycle", response=response_schema, auth=AuthBearer())
def update_cycle(request, cycle_id, data: UpdateCycleSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return CycleService().update_cycle(cycle_id, data)


@router.delete("/delete-cycle", response=response_schema, auth=AuthBearer())
def delete_cycle(request, cycle_id):
    user = get_signed_in_user(request)
    return CycleService().delete_cycle(cycle_id, str(user.id))

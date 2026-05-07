# pylint: disable=missing-function-docstring, unused-argument

from ninja import Body, Router

from teramina.authentication.auth_bearer import AuthBearer
from teramina.pond.schemas.pond_schema import PondDataSchema, UpdatePondSchema
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema
from teramina.pond.services.pond_service import PondService
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_farm_owner, verify_pond_owner

router = Router(tags=["Pond"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/add-pond", response=response_schema, auth=AuthBearer())
def add_pond(request, farm_id, data: PondDataSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return PondService.add_pond(farm_id, data)


@router.get("/list-pond", response=response_schema, auth=AuthBearer())
def list_pond(request, farm_id, page: int = 1, limit: int = 100):
    user = get_signed_in_user(request)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return PondService.get_pond(farm_id, page=page, limit=limit)


@router.put("/update-pond", response=response_schema, auth=AuthBearer())
def update_pond(request, pond_id, data: UpdatePondSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_pond_owner(pond_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return PondService.update_pond(pond_id, data)


@router.delete("/delete-pond", response=response_schema, auth=AuthBearer())
def delete_pond(request, pond_id):
    user = get_signed_in_user(request)
    return PondService.delete_pond(pond_id, str(user.id))

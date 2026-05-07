# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from ..schemas.farm_schema import FarmDataSchema

from ...schemas.general_schema import (
    DataErrorSchema,
    DataSuccessSchema,
    GetListSuccessSchema,
)

from ..services.farm_service import FarmService
from ...authentication.auth_bearer import AuthBearer
from ...authentication.services.authentication_service import get_signed_in_user
from ...helpers.ownership import verify_farm_owner

router = Router(tags=["Farm"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.post("/add-farm", response=response_schema, auth=AuthBearer())
def add_farm(request, data: FarmDataSchema = Body(...)):
    user = get_signed_in_user(request)
    return FarmService.add_farm(user.id, data)


@router.get(
    "/list-farm",
    response={200: GetListSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema},
    auth=AuthBearer(),
)
def list_farm(request, page: int = 1, limit: int = 50):
    user = get_signed_in_user(request)
    return FarmService().get_all_farm(user_id=user.id, page=page, limit=limit)


@router.put("/update-farm", response=response_schema, auth=AuthBearer())
def update_farm(request, farm_id, data: FarmDataSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return FarmService.update_farm(farm_id, data)


@router.delete("/delete-farm", response=response_schema, auth=AuthBearer())
def delete_farm(request, farm_id):
    user = get_signed_in_user(request)
    return FarmService.delete_farm(farm_id=farm_id, user_id=str(user.id))

# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body

from ..services.registration_service import RegistrationService
from ..schemas.registration_schema import BetaAccessRequestCreateSchema, BetaAccessRequestUpdateSchema, RegisterSchema
from ...authentication.auth_bearer import AuthBearer
from ...authentication.services.authentication_service import get_signed_in_user
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema

router = Router(tags=["Registration"])
response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/register", response=response_schema)
def register(request, data: RegisterSchema = Body(...)):
    registration_service = RegistrationService()
    return registration_service.register(data)


@router.post("/access-requests", response=response_schema)
def request_beta_access(request, data: BetaAccessRequestCreateSchema = Body(...)):
    return RegistrationService.request_beta_access(data)


@router.get("/admin/access-requests", response=response_schema, auth=AuthBearer())
def list_beta_access_requests(request):
    return RegistrationService.list_beta_access_requests(get_signed_in_user(request))


@router.patch("/admin/access-requests/{request_id}", response=response_schema, auth=AuthBearer())
def update_beta_access_request(request, request_id: str, data: BetaAccessRequestUpdateSchema = Body(...)):
    return RegistrationService.update_beta_access_request(get_signed_in_user(request), request_id, data)

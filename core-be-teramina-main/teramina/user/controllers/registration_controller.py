# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body

from ..services.registration_service import RegistrationService
from ..schemas.registration_schema import RegisterSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema

router = Router(tags=["Registration"])
response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/register", response=response_schema)
def register(request, data: RegisterSchema = Body(...)):
    registration_service = RegistrationService()
    return registration_service.register(data)

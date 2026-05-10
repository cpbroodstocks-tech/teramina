# pylint: disable=missing-function-docstring
from ninja import Router

from teramina.authentication.auth_bearer import AuthBearer
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_farm_owner
from teramina.pl_report.services.farm_pl_service import FarmProfitLossService

router = Router(tags=["P&L Report"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.get("/report/pl", response=response_schema, auth=AuthBearer())
def get_farm_pl_report(request, farm_id: str):
    user = get_signed_in_user(request)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    try:
        report = FarmProfitLossService(farm_id).get_report()
        return 200, DataSuccessSchema(code=200, message="OK", payload=report)
    except ValueError as exc:
        return 400, DataErrorSchema(code=400, message=str(exc))

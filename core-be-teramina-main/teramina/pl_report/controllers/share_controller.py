# pylint: disable=missing-function-docstring
from ninja import Router

from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema
from teramina.pl_report.models.share_token_model import PLReportShareToken
from teramina.pl_report.services.pl_report_service import ProfitLossService

router = Router(tags=["P&L Report – Public"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 404: DataErrorSchema}


@router.get("/share/{token}", response=response_schema)
def get_shared_pl_report(request, token: str):
    share = PLReportShareToken.objects(token=token).first()
    if not share:
        return 404, DataErrorSchema(code=404, message="Link not found")
    if not share.is_valid():
        return 400, DataErrorSchema(code=400, message="Link has expired")
    try:
        report = ProfitLossService(share.cycle_id).get_report()
        return 200, DataSuccessSchema(code=200, message="OK", payload=report)
    except ValueError as exc:
        return 400, DataErrorSchema(code=400, message=str(exc))

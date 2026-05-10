# pylint: disable=missing-function-docstring
from django.http import HttpResponse
from ninja import Router

from teramina.authentication.auth_bearer import AuthBearer
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from teramina.pl_report.services.pl_report_service import ProfitLossService
from teramina.pl_report.services.pl_pdf_service import build_pl_pdf
from teramina.pl_report.services.pl_excel_service import build_pl_excel
from teramina.pl_report.services.pl_narrative_service import build_pl_narrative
from teramina.pl_report.services.pl_bank_pdf_service import build_bank_pdf
from teramina.pl_report.models.share_token_model import PLReportShareToken

router = Router(tags=["P&L Report"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.get("/report/pl", response=response_schema, auth=AuthBearer())
def get_pl_report(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    try:
        report = ProfitLossService(cycle_id).get_report()
        return 200, DataSuccessSchema(code=200, message="OK", payload=report)
    except ValueError as exc:
        return 400, DataErrorSchema(code=400, message=str(exc))


@router.get("/report/pl/pdf", auth=AuthBearer())
def download_pl_pdf(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return HttpResponse("Unauthorized", status=401)
    try:
        report = ProfitLossService(cycle_id).get_report()
        pdf_bytes = build_pl_pdf(report)
        filename = f"pl_report_{report['cycle_name'].replace(' ', '_')}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except ValueError as exc:
        return HttpResponse(str(exc), status=400)


@router.get("/report/pl/excel", auth=AuthBearer())
def download_pl_excel(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return HttpResponse("Unauthorized", status=401)
    try:
        report = ProfitLossService(cycle_id).get_report()
        xlsx_bytes = build_pl_excel(report)
        filename = f"pl_report_{report['cycle_name'].replace(' ', '_')}.xlsx"
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response = HttpResponse(xlsx_bytes, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except ValueError as exc:
        return HttpResponse(str(exc), status=400)


@router.get("/report/pl/narrative", response=response_schema, auth=AuthBearer())
def get_pl_narrative(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    try:
        report = ProfitLossService(cycle_id).get_report()
        narrative = build_pl_narrative(report)
        return 200, DataSuccessSchema(code=200, message="OK", payload={"narrative": narrative})
    except Exception as exc:  # pylint: disable=broad-except
        return 400, DataErrorSchema(code=400, message=str(exc))


@router.get("/report/pl/pdf/bank", auth=AuthBearer())
def download_bank_pdf(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return HttpResponse("Unauthorized", status=401)
    try:
        report = ProfitLossService(cycle_id).get_report()
        pdf_bytes = build_bank_pdf(report)
        filename = f"pl_bank_{report['cycle_name'].replace(' ', '_')}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except ValueError as exc:
        return HttpResponse(str(exc), status=400)


@router.post("/report/pl/share", response=response_schema, auth=AuthBearer())
def create_share_link(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    try:
        share = PLReportShareToken.create_for_cycle(cycle_id)
        return 200, DataSuccessSchema(
            code=200,
            message="Share link created",
            payload={
                "token": share.token,
                "expires_at": share.expires_at.isoformat(),
            },
        )
    except Exception as exc:  # pylint: disable=broad-except
        return 400, DataErrorSchema(code=400, message=str(exc))

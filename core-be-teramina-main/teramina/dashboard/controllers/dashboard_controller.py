# pylint: disable=missing-function-docstring, unused-argument, E0401

import base64
from io import BytesIO
from celery.result import AsyncResult
from django.core.cache import cache
from ninja import Router
from django.http import HttpResponse, JsonResponse

from teramina.schemas.general_schema import (
    DataErrorSchema,
    DataSuccessSchema,
    GetListSuccessSchema,
)
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.authentication.auth_bearer import AuthBearer
from teramina.helpers.ownership import verify_cycle_owner, verify_farm_owner, verify_pond_owner

from teramina.dashboard.services.historical.overview import DashboardOverview
from teramina.dashboard.services.historical.economic import DashboardEconomic
from teramina.dashboard.services.historical.feed import DashboardFeed

from teramina.dashboard.services.filter_service import FilterData
from teramina.dashboard.services.forecast_service import ForecastDataService

from teramina.helpers.report_service import generate_pdf_report_with_data
from teramina.dashboard.tasks.report_tasks import generate_overview_report

router = Router(tags=["Dashboard"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}
REPORT_TASK_OWNER_TTL = 60 * 60


def _report_task_owner_key(task_id):
    return f"dashboard_report_owner:{task_id}"


def _owns_dashboard_context(user_id, farm_id="", pond_id="", cycle_id=""):
    return (
        bool(farm_id)
        and verify_farm_owner(farm_id, user_id)
        and (not pond_id or verify_pond_owner(pond_id, user_id))
        and (not cycle_id or verify_cycle_owner(cycle_id, user_id))
    )


@router.get("/overview", response=response_schema, auth=AuthBearer())
def overview(request, farm_id, pond_id=None, cycle_id=None, date=None):
    user = get_signed_in_user(request)
    if not _owns_dashboard_context(str(user.id), farm_id, pond_id, cycle_id):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return DashboardOverview(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date
    ).overview()


@router.get("/economics", response=response_schema, auth=AuthBearer())
def economics(request, farm_id, pond_id=None, cycle_id=None, date=None):
    user = get_signed_in_user(request)
    if not _owns_dashboard_context(str(user.id), farm_id, pond_id, cycle_id):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return DashboardEconomic(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date
    ).economic()


@router.get("/feeding", response=response_schema, auth=AuthBearer())
def feeding(request, farm_id, pond_id=None, cycle_id=None, date=None):
    user = get_signed_in_user(request)
    if not _owns_dashboard_context(str(user.id), farm_id, pond_id, cycle_id):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return DashboardFeed(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date
    ).feed()


@router.get("/forecast", response=response_schema, auth=AuthBearer())
def forecast(request, cycle_id=None, date=None):
    user = get_signed_in_user(request)
    if not cycle_id or not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return ForecastDataService().get_forecasting_overview(cycle_id=cycle_id, date=date)


@router.get(
    "/filter",
    response={200: GetListSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema},
    auth=AuthBearer(),
)
def filter_data(
    request, farm_id=None, pond_id=None, cycle_id=None, filter_type="historical"
):
    user = get_signed_in_user(request)
    return FilterData(str(user.id)).filter(farm_id, pond_id, cycle_id, filter_type)


@router.get(
    "/wq-filter",
    response={200: GetListSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema},
    auth=AuthBearer(),
)
def wq_filter_data(request, farm_id=None, pond_id=None, cycle_id=None):
    user = get_signed_in_user(request)
    return FilterData(str(user.id)).wq_filter(farm_id, pond_id, cycle_id)


@router.get("/download-pdf-report", auth=AuthBearer())
async def download_pdf_report(request, farm_id, pond_id=None, cycle_id=None, date=None):
    user = get_signed_in_user(request)
    if not _owns_dashboard_context(str(user.id), farm_id, pond_id, cycle_id):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    dashboard = DashboardOverview(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date,
        user_id=str(user.id),
    )

    async def run_process():
        # Get report contents asynchronously
        contents = await dashboard.download_report_pdf()
        # Generate PDF report
        pdf_output = generate_pdf_report_with_data(contents)

        # Save PDF to response buffer
        pdf_buffer = BytesIO(pdf_output)

        # Create HttpResponse
        response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="report_teramina.pdf"'

        return response

    # Start the process asynchronously
    response = await run_process()
    return response


@router.post("/create-report", auth=AuthBearer())
def create_report(request, payload: dict):
    user = get_signed_in_user(request)
    if not _owns_dashboard_context(
        str(user.id), payload.get("farm_id"), payload.get("pond_id"), payload.get("cycle_id")
    ):
        return JsonResponse({"code": 401, "message": "Unauthorized"}, status=401)
    task = generate_overview_report.delay(
        payload.get("farm_id"),
        payload.get("pond_id"),
        payload.get("cycle_id"),
        payload.get("date") or None,
        str(user.id),
    )
    cache.set(_report_task_owner_key(task.id), str(user.id), timeout=REPORT_TASK_OWNER_TTL)
    return {"task_id": task.id}


@router.get("/get-report/{task_id}", auth=AuthBearer())
def get_report(request, task_id: str):
    user = get_signed_in_user(request)
    owner_key = _report_task_owner_key(task_id)
    if cache.get(owner_key) != str(user.id):
        return JsonResponse({"code": 404, "message": "Report task not found"}, status=404)

    result = AsyncResult(task_id)

    if result.state in ("PENDING", "STARTED", "RETRY"):
        return JsonResponse({"status": result.state})

    if result.state == "FAILURE":
        cache.delete(owner_key)
        return JsonResponse(
            {"status": "FAILURE", "error": str(result.result)},
            status=500,
        )

    payload = result.result or {}
    if not isinstance(payload, dict) or not payload.get("data_base64"):
        cache.delete(owner_key)
        return JsonResponse(
            {"status": "FAILURE", "error": "Report result is unavailable"},
            status=500,
        )

    pdf_bytes = base64.b64decode(payload["data_base64"])
    response = HttpResponse(
        pdf_bytes,
        content_type=payload.get("content_type", "application/pdf"),
    )
    filename = payload.get("filename", "report_teramina.pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    cache.delete(owner_key)
    return response

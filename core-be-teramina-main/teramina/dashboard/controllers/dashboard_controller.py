# pylint: disable=missing-function-docstring, unused-argument, E0401

from io import BytesIO
from ninja import Router
from django.http import HttpResponse

from teramina.schemas.general_schema import (
    DataErrorSchema,
    DataSuccessSchema,
    GetListSuccessSchema,
)
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.authentication.auth_bearer import AuthBearer

from teramina.dashboard.services.historical.overview import DashboardOverview
from teramina.dashboard.services.historical.economic import DashboardEconomic
from teramina.dashboard.services.historical.feed import DashboardFeed

from teramina.dashboard.services.filter_service import FilterData
from teramina.dashboard.services.forecast_service import ForecastDataService

from teramina.helpers.report_service import generate_pdf_report_with_data

router = Router(tags=["Dashboard"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.get("/overview", response=response_schema, auth=AuthBearer())
def overview(request, farm_id, pond_id=None, cycle_id=None, date=None):
    return DashboardOverview(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date
    ).overview()


@router.get("/economics", response=response_schema, auth=AuthBearer())
def economics(request, farm_id, pond_id=None, cycle_id=None, date=None):
    return DashboardEconomic(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date
    ).economic()


@router.get("/feeding", response=response_schema, auth=AuthBearer())
def feeding(request, farm_id, pond_id=None, cycle_id=None, date=None):
    return DashboardFeed(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date
    ).feed()


@router.get("/forecast", response=response_schema, auth=AuthBearer())
def forecast(request, cycle_id=None, date=None):
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
    dashboard = DashboardOverview(
        farm_id=farm_id, pond_id=pond_id, cycle_id=cycle_id, date=date
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

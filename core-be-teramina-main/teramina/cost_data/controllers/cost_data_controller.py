# pylint: disable=missing-function-docstring, unused-argument,E0401
from io import BytesIO
from django.http import HttpResponse
from ninja import Router, File, Form  # , Query
from ninja.files import UploadedFile
from teramina.cost_data.services.cost_data_service import CostDataService
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner, verify_farm_owner

router = Router(tags=["Cost"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.post("/add-cost-data", response=response_schema, auth=AuthBearer())
def add_cost_data(
    request, cycle_id, labels: list[str] = Form(...), files: list[UploadedFile] = File(...)
):
    """add cost data endpoint"""
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return CostDataService(cycle_id).add_data(labels, files)


@router.post("/add-single-cost-data", response=response_schema, auth=AuthBearer())
def add_single_cost_data(
    request, farm_id, start_date, end_date, file: UploadedFile = File(...)
):
    """add cost data endpoint"""
    user = get_signed_in_user(request)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return CostDataService.add_single_data(farm_id, start_date, end_date, file)

@router.get("/download-pl-report", response=response_schema, auth=AuthBearer())
def download_single_cost_data(request, farm_id):
    """download data"""
    user = get_signed_in_user(request)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    try:
        work_book = CostDataService.download_single_data(farm_id)
    except ValueError as exception:
        return 400, DataErrorSchema(code=400, message=str(exception))

    with BytesIO() as buffer:
        work_book.save(buffer)
        buffer.seek(0)

        # Create the HttpResponse
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=pl_report.xlsx'

        return response

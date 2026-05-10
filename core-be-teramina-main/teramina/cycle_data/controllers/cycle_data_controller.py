# pylint: disable=missing-function-docstring, unused-argument
from django.http import HttpResponse
from ninja import Router, File  # , Query
from ninja.files import UploadedFile

# import openpyxl
# import pandas as pd
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from ...schemas.general_schema import DataSuccessSchema, DataErrorSchema
from ..services.cycle_data_service import CycleService
from ..services.quality_report_service import get_quality_report
from ...helpers.ownership import verify_cycle_owner, verify_farm_owner
from ...helpers.file_validation import validate_csv_file

router = Router(tags=["Cycle Data Management"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.post("/populate-cycle-data", response=response_schema, auth=AuthBearer())
def populate_cycle_data(
    request, cycle_id, file: UploadedFile = File(...), source_type="csv"
):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    file_error = validate_csv_file(file)
    if file_error:
        return 400, DataErrorSchema(code=400, message=file_error)
    return CycleService().add_cycle_data(
        cycle_id, file, user_id=user.id, source_type=source_type
    )


@router.get("/list-cycle-data", response=response_schema, auth=AuthBearer())
def get_cycle_data(request, cycle_id):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return CycleService().get_cycle_data(cycle_id)


@router.get("/download-cycle_data", auth=AuthBearer())
def download_cycle_data(request, cycle_id):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return HttpResponse("Unauthorized", status=401)
    df = CycleService().get_cycle_dataframe(cycle_id)
    csv_buffer = df.to_csv(index=False, encoding="utf-8")
    response = HttpResponse(csv_buffer, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="data.csv"'
    return response

@router.get("/download-cycle_data_by_farm", auth=AuthBearer())
def download_cycle_data_filter(request, farm_id):
    user = get_signed_in_user(request)
    if not verify_farm_owner(farm_id, str(user.id)):
        return HttpResponse("Unauthorized", status=401)
    df = CycleService().get_cycle_dataframe_by_filter(user.email, farm_id)
    csv_buffer = df.to_csv(index=False, encoding="utf-8")
    response = HttpResponse(csv_buffer, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="data.csv"'
    return response

@router.get("/get-last-data", auth=AuthBearer())
def get_last_data(request, cycle_id):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return CycleService().get_last_data(cycle_id)


@router.get("/quality-report", response=response_schema, auth=AuthBearer())
def quality_report(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    result = get_quality_report(cycle_id)
    if "error" in result:
        return 400, DataErrorSchema(code=400, message=result["error"])
    return 200, DataSuccessSchema(code=200, message="OK", payload=result)


# @router.get("/download-cycle-data-xlsx")
# def download_cycle_data_excel(request, cycle_id):
#     df = CycleService().get_cycle_dataframe(cycle_id)
#     response = HttpResponse(
#         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
#     response["Content-Disposition"] = "attachment; filename=data.xlsx"
#     # Write the DataFrame to an XLSX file and save it to the response
#     with pd.ExcelWriter(response, engine="openpyxl") as writer:
#         writer.book = openpyxl.Workbook()
#         df.to_excel(writer, sheet_name="Sheet1", index=False)
#     return response


# @router.get("/select-variables")
# def select_variables(
#     request,
#     farm: str = Query(...),
#     pond: str = Query(...),
#     cycles: str = Query(...),
#     start_date: str = Query(...),
#     end_date: str = Query(...),
#     variables: str = Query(...),
# ):
#     variable = variables.split(",")
#     return {"variables": variable}

# pylint: disable=missing-function-docstring, unused-argument, E0402, E0110

from ninja import Router
from django.http import HttpResponse, FileResponse
import pandas as pd
import openpyxl
from ...authentication.auth_bearer import AuthBearer
from ...authentication.services.authentication_service import get_signed_in_user
from ...helpers.ownership import verify_cycle_owner
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema
from ..services.water_quality_service import WaterQuality

router = Router(tags=["Water Quality Data"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


def _owns_cycles(request, cycles):
    user = get_signed_in_user(request)
    cycle_ids = [cycle_id.strip() for cycle_id in cycles.split(",") if cycle_id.strip()]
    return bool(cycle_ids) and all(verify_cycle_owner(cycle_id, str(user.id)) for cycle_id in cycle_ids)


@router.get("/get-water-quality-dashboard", response=response_schema, auth=AuthBearer())
def get_water_quality_dashboard(request, cycles, start_date, end_date, variables):
    if not _owns_cycles(request, cycles):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return WaterQuality().get_water_quality_data(
        cycles, start_date, end_date, variables
    )


@router.get("/download-water-quality-xlsx", response=response_schema, auth=AuthBearer())
def download_xlsx(request, cycles, start_date, end_date, variables):
    if not _owns_cycles(request, cycles):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    df = WaterQuality().get_table(cycles, start_date, end_date, variables)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=data.xlsx"
    # Write the DataFrame to an XLSX file and save it to the response
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        writer.book = openpyxl.Workbook()
        df.to_excel(writer, sheet_name="Sheet1", index=False)
    return response


@router.get("/download-water-quality-csv", response=response_schema, auth=AuthBearer())
def download_csv(request, cycles, start_date, end_date, variables):
    if not _owns_cycles(request, cycles):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    df = WaterQuality().get_table(cycles, start_date, end_date, variables)
    csv_buffer = df.to_csv(index=False, encoding="utf-8")
    response = HttpResponse(csv_buffer, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="data.csv"'
    return response


@router.get("/generate-pdf/", response=response_schema, auth=AuthBearer())
def generate_pdf(request, cycles, start_date, end_date, variables):
    if not _owns_cycles(request, cycles):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    # Create a BytesIO buffer to receive the PDF data.
    df = WaterQuality().get_table(cycles, start_date, end_date, variables)
    buffer = WaterQuality().get_plot_document(df, variables)
    response = FileResponse(
        buffer,
        as_attachment=True,
        filename=f"waterquality_dashboard_{start_date}_{end_date}.pdf",
    )
    return response

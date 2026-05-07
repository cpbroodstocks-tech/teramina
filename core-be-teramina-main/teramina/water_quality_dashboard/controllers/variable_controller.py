# pylint: disable=missing-function-docstring, unused-argument, E0402

from ninja import Body, Router

from teramina.authentication.auth_bearer import AuthBearer
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema
from ..services.variable_management import AddVariableSchema, VariableManagement

router = Router(tags=["Water Quality Variable"])

response_schema = {200: DataSuccessSchema, 401: DataErrorSchema, 400: DataErrorSchema}


@router.post("/update-variable", response=response_schema, auth=AuthBearer())
def update_variable(request, data: AddVariableSchema = Body(...)):
    return VariableManagement().add_variable(data)


@router.get("/view-variable", response=response_schema, auth=AuthBearer())
def get_single_variable(request, var_name):
    return VariableManagement().get_water_quality_var(var_name)


@router.get("/get-variable", response=response_schema, auth=AuthBearer())
def get_variable(request):
    return VariableManagement().get_water_quality_vars()

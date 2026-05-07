# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_farm_owner
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema
from teramina.cycle.models.cycle_model import Cycle
from teramina.pond.models.pond_model import Pond

from ..schemas.benchmark_schema import OptInSchema
from ..services.benchmark_service import BenchmarkService

router = Router(tags=["Benchmarking"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/opt-in", response=response_schema, auth=AuthBearer())
def opt_in(request, data: OptInSchema = Body(...)):
    user = get_signed_in_user(request)
    cycle = Cycle.objects(id=data.cycle_id).first()
    if not cycle:
        return 400, DataErrorSchema(code=400, message="Cycle not found")
    pond = Pond.objects(id=cycle.pond_id).first()
    if not pond:
        return 400, DataErrorSchema(code=400, message="Pond not found")
    farm_id = str(pond.farm_id)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return BenchmarkService.opt_in(farm_id, str(user.id))


@router.post("/opt-out", response=response_schema, auth=AuthBearer())
def opt_out(request, data: OptInSchema = Body(...)):
    user = get_signed_in_user(request)
    cycle = Cycle.objects(id=data.cycle_id).first()
    if not cycle:
        return 400, DataErrorSchema(code=400, message="Cycle not found")
    pond = Pond.objects(id=cycle.pond_id).first()
    if not pond:
        return 400, DataErrorSchema(code=400, message="Pond not found")
    farm_id = str(pond.farm_id)
    if not verify_farm_owner(farm_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return BenchmarkService.opt_out(farm_id)


@router.get("/my-performance", response=response_schema, auth=AuthBearer())
def my_performance(request, cycle_id: str):
    user = get_signed_in_user(request)
    return BenchmarkService.get_my_performance(cycle_id, str(user.id))

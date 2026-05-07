# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..models.sheet_integration_model import SheetIntegration
from ..schemas.sheet_schema import ConnectSheetSchema
from ..services.sheet_service import SheetService
from ..tasks.sync_tasks import sync_single_cycle

router = Router(tags=["Google Sheets"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/connect", response=response_schema, auth=AuthBearer())
def connect_sheet(request, data: ConnectSheetSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(data.cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return SheetService.connect(str(user.id), data.cycle_id, data.spreadsheet_id)


@router.delete("/disconnect", response=response_schema, auth=AuthBearer())
def disconnect_sheet(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return SheetService.disconnect(cycle_id)


@router.get("/status", response=response_schema, auth=AuthBearer())
def sheet_status(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return SheetService.get_status(cycle_id)


@router.post("/manual-sync", response=response_schema, auth=AuthBearer())
def manual_sync(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    # Mark as syncing before queuing so frontend can poll for completion
    integration = SheetIntegration.objects(cycle_id=cycle_id, is_active=True).first()
    if not integration:
        return 400, DataErrorSchema(code=400, message="No active sheet integration found")
    integration.last_status = "syncing"
    integration.save()
    sync_single_cycle.delay(cycle_id)
    return 200, DataSuccessSchema(code=200, message="Sync queued", payload={"cycle_id": cycle_id})


@router.post("/create-template", response=response_schema, auth=AuthBearer())
def create_template(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return SheetService.create_template(
        cycle_id,
        user_id=str(user.id),
        user_email=getattr(user, "email", None),
    )

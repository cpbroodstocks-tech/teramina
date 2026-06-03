# pylint: disable=missing-function-docstring, unused-argument

import uuid
from datetime import datetime, timedelta

from django.core.cache import cache
from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..models.sheet_integration_model import SheetIntegration
from ..models.sync_log_model import SheetSyncLog
from ..schemas.sheet_schema import ConnectSheetSchema, SheetSyncLogSchema, PreviewSyncResult
from ..services.sheet_service import SheetService, SYNC_LOCK_KEY_PREFIX
from ..tasks.sync_tasks import VALID_IMPORT_MODES, sync_single_cycle

router = Router(tags=["Google Sheets"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}

_PREVIEW_TTL = 600  # seconds (10 minutes)
_MANUAL_SYNC_RATE_LIMIT_SECONDS = 60


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


@router.get("/sync-log", response=response_schema, auth=AuthBearer())
def get_sync_log(request, cycle_id: str, sync_id: str = ""):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")

    filters = {"cycle_id": cycle_id}
    if sync_id:
        try:
            filters["sync_id"] = uuid.UUID(sync_id)
        except ValueError:
            return 400, DataErrorSchema(code=400, message="Invalid sync_id")
    log = SheetSyncLog.objects(**filters).first()
    if not log:
        message = "No sync log found for this sync" if sync_id else "No sync log found for this cycle"
        return 404, DataErrorSchema(code=404, message=message)

    return 200, DataSuccessSchema(
        code=200,
        message="OK",
        payload=SheetSyncLogSchema(
            sync_id=str(log.sync_id),
            cycle_id=log.cycle_id,
            spreadsheet_id=getattr(log, "spreadsheet_id", None),
            source_fingerprint=getattr(log, "source_fingerprint", None),
            started_at=log.started_at,
            finished_at=log.finished_at,
            duration_seconds=getattr(log, "duration_seconds", None),
            rows_per_second=getattr(log, "rows_per_second", None),
            status=log.status,
            error_category=getattr(log, "error_category", None),
            tab_summaries=[
                {
                    "tab": ts.tab, "processed": ts.processed,
                    "inserted": ts.inserted, "updated": ts.updated,
                    "deleted": getattr(ts, "deleted", 0),
                    "skipped": ts.skipped, "rejected": ts.rejected,
                    "error": getattr(ts, "error", None),
                    "error_category": getattr(ts, "error_category", None),
                }
                for ts in log.tab_summaries
            ],
            rejected_rows=[
                {
                    "tab": r.tab, "row_number": r.row_number,
                    "field": r.field, "raw_value": r.raw_value, "reason": r.reason,
                }
                for r in log.rejected_rows
            ],
        ).dict(),
    )


@router.post("/manual-sync", response=response_schema, auth=AuthBearer())
def manual_sync(request, cycle_id: str, import_mode: str = "valid_rows_only"):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    if import_mode not in VALID_IMPORT_MODES:
        return 400, DataErrorSchema(code=400, message=f"Unsupported import mode: {import_mode}")
    # Mark as syncing before queuing so frontend can poll for completion
    integration = SheetIntegration.objects(cycle_id=cycle_id, is_active=True).first()
    if not integration:
        return 400, DataErrorSchema(code=400, message="No active sheet integration found")
    if cache.get(f"{SYNC_LOCK_KEY_PREFIX}{cycle_id}"):
        return 400, DataErrorSchema(code=400, message="Sync already in progress")
    rate_key = f"sheet_manual_sync_rate:{user.id}:{cycle_id}"
    if not cache.add(rate_key, "1", timeout=_MANUAL_SYNC_RATE_LIMIT_SECONDS):
        return 400, DataErrorSchema(code=400, message="Please wait before starting another manual sync")
    sync_id = uuid.uuid4()
    integration.last_status = "queued"
    integration.active_sync_id = sync_id
    integration.save()
    sync_single_cycle.delay(cycle_id, None, str(sync_id), import_mode)
    return 200, DataSuccessSchema(
        code=200,
        message="Sync queued",
        payload={
            "cycle_id": cycle_id,
            "sync_id": str(sync_id),
            "status": "queued",
            "import_mode": import_mode,
        },
    )


@router.post("/preview-sync", response=response_schema, auth=AuthBearer())
def preview_sync(request, cycle_id: str, import_mode: str = "valid_rows_only"):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    if import_mode not in VALID_IMPORT_MODES:
        return 400, DataErrorSchema(code=400, message=f"Unsupported import mode: {import_mode}")

    integration = SheetIntegration.objects(cycle_id=cycle_id, is_active=True).first()
    if not integration:
        return 400, DataErrorSchema(code=400, message="No active sheet integration found")

    result = SheetService.sync_cycle(cycle_id, dry_run=True)
    if "error" in result:
        return 400, DataErrorSchema(code=400, message=result["error"])

    preview_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(seconds=_PREVIEW_TTL)

    summary = result.get("summary", {})
    rejected_rows = result.get("rejected_rows", [])

    # Count rows_valid, rows_warning, rows_error from summary + rejected_rows
    rows_warning = sum(
        1 for r in rejected_rows if r.get("reason", "").startswith("warn:")
    )
    rows_error = sum(
        1 for r in rejected_rows if not r.get("reason", "").startswith("warn:")
    )
    rows_valid = sum(
        v.get("inserted", 0) + v.get("updated", 0)
        for v in summary.values() if "error" not in v
    )

    tab_summaries = [
        {
            "tab": tab,
            "processed": (
                v.get("inserted", 0) + v.get("updated", 0) + v.get("deleted", 0)
                + v.get("skipped", 0) + v.get("rejected", 0)
            ),
            "inserted": v.get("inserted", 0),
            "updated": v.get("updated", 0),
            "deleted": v.get("deleted", 0),
            "skipped": v.get("skipped", 0),
            "rejected": v.get("rejected", 0),
            "error": v.get("error"),
        }
        for tab, v in summary.items() if "error" not in v
    ]

    if import_mode == "strict" and rows_error > 0:
        return 400, DataErrorSchema(
            code=400,
            message="Strict import blocked because the sheet has errors.",
        )

    payload = PreviewSyncResult(
        preview_id=preview_id,
        expires_at=expires_at,
        rows_valid=rows_valid,
        rows_warning=rows_warning,
        rows_error=rows_error,
        tab_summaries=tab_summaries,
        rejected_rows=rejected_rows,
    ).dict()

    cache.set(
        f"sheet_preview:{preview_id}",
        {
            "cycle_id": cycle_id,
            "source_fingerprint": result.get("source_fingerprint"),
            "import_mode": import_mode,
        },
        timeout=_PREVIEW_TTL,
    )

    return 200, DataSuccessSchema(code=200, message="Preview ready", payload=payload)


@router.post("/confirm-sync", response=response_schema, auth=AuthBearer())
def confirm_sync(request, preview_id: str):
    user = get_signed_in_user(request)

    cached = cache.get(f"sheet_preview:{preview_id}")
    if not cached:
        return 400, DataErrorSchema(code=400, message="Preview expired or not found. Run preview-sync again.")

    cycle_id = cached["cycle_id"]
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")

    # Consume preview token (one-time use)
    cache.delete(f"sheet_preview:{preview_id}")

    integration = SheetIntegration.objects(cycle_id=cycle_id, is_active=True).first()
    if not integration:
        return 400, DataErrorSchema(code=400, message="No active sheet integration found")
    if cache.get(f"{SYNC_LOCK_KEY_PREFIX}{cycle_id}"):
        return 400, DataErrorSchema(code=400, message="Sync already in progress")

    sync_id = uuid.uuid4()
    integration.last_status = "queued"
    integration.active_sync_id = sync_id
    integration.save()
    import_mode = cached.get("import_mode", "valid_rows_only")
    sync_single_cycle.delay(cycle_id, cached.get("source_fingerprint"), str(sync_id), import_mode)

    return 200, DataSuccessSchema(
        code=200,
        message="Import confirmed and queued",
        payload={
            "cycle_id": cycle_id,
            "preview_id": preview_id,
            "sync_id": str(sync_id),
            "status": "queued",
            "import_mode": import_mode,
        },
    )


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

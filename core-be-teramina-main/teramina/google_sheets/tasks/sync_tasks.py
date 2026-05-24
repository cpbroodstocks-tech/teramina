# pylint: disable=broad-except

import logging
from celery import shared_task
from django.core.cache import cache
from ..models.sheet_integration_model import SheetIntegration
from ..services.sheet_service import SheetService, SYNC_LOCK_KEY_PREFIX

logger = logging.getLogger("teramina")

VALID_IMPORT_MODES = {"valid_rows_only", "strict"}


def _has_strict_errors(result: dict) -> bool:
    summary = result.get("summary", {})
    if any("error" in data for data in summary.values()):
        return True
    return any(
        not row.get("reason", "").startswith("warn:")
        for row in result.get("rejected_rows", [])
    )


def _mark_sync_error(cycle_id: str, message: str):
    integration = SheetIntegration.objects(cycle_id=cycle_id, is_active=True).first()
    if integration:
        integration.last_status = "error"
        integration.last_error = message
        integration.active_sync_id = None
        integration.save()


def _run_sync_with_lock(
    cycle_id: str,
    expected_fingerprint: str = None,
    sync_id: str = None,
    import_mode: str = "valid_rows_only",
):
    if import_mode not in VALID_IMPORT_MODES:
        return {"error": f"Unsupported import mode: {import_mode}"}

    lock_key = f"{SYNC_LOCK_KEY_PREFIX}{cycle_id}"
    if not cache.add(lock_key, "1", timeout=900):
        logger.info("Sheet sync skipped: lock active cycle=%s sync_id=%s", cycle_id, sync_id)
        return {"error": "Sync already in progress"}
    try:
        logger.info(
            "Sheet sync started cycle=%s sync_id=%s import_mode=%s",
            cycle_id,
            sync_id,
            import_mode,
        )
        if import_mode == "strict":
            preview = SheetService.sync_cycle(cycle_id, dry_run=True)
            if "error" in preview:
                _mark_sync_error(cycle_id, preview["error"])
                return preview
            if _has_strict_errors(preview):
                message = "Strict import blocked because the sheet has errors."
                _mark_sync_error(cycle_id, message)
                return {"error": message, **preview}
            expected_fingerprint = preview.get("source_fingerprint")

        result = SheetService.sync_cycle(
            cycle_id,
            expected_fingerprint=expected_fingerprint,
            sync_id=sync_id,
        )
        logger.info(
            "Sheet sync finished cycle=%s sync_id=%s status=%s",
            cycle_id,
            sync_id,
            result.get("status") or result.get("error"),
        )
        return result
    finally:
        cache.delete(lock_key)


@shared_task(name="google_sheets.sync_all_active_sheets")
def sync_all_active_sheets():
    """Celery Beat task: sync all active sheet integrations."""
    integrations = SheetIntegration.objects(is_active=True).only("cycle_id")
    synced = 0
    errors = 0
    for integration in integrations:
        try:
            result = _run_sync_with_lock(integration.cycle_id)
            if result.get("error"):
                errors += 1
            else:
                synced += 1
        except Exception as exc:
            logger.error("Sync failed for cycle %s: %s", integration.cycle_id, exc)
            errors += 1
    logger.info("Sheet sync complete: %d synced, %d errors", synced, errors)
    return {"synced": synced, "errors": errors}


@shared_task(name="google_sheets.sync_single_cycle")
def sync_single_cycle(
    cycle_id: str,
    expected_fingerprint: str = None,
    sync_id: str = None,
    import_mode: str = "valid_rows_only",
):
    """Celery task: sync one specific cycle's sheet."""
    return _run_sync_with_lock(cycle_id, expected_fingerprint, sync_id, import_mode)

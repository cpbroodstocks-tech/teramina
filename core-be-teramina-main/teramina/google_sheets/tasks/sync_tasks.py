# pylint: disable=broad-except

import logging
from celery import shared_task
from ..models.sheet_integration_model import SheetIntegration
from ..services.sheet_service import SheetService

logger = logging.getLogger("teramina")


@shared_task(name="google_sheets.sync_all_active_sheets")
def sync_all_active_sheets():
    """Celery Beat task: sync all active sheet integrations."""
    integrations = SheetIntegration.objects(is_active=True).only("cycle_id")
    synced = 0
    errors = 0
    for integration in integrations:
        try:
            SheetService.sync_cycle(integration.cycle_id)
            synced += 1
        except Exception as exc:
            logger.error("Sync failed for cycle %s: %s", integration.cycle_id, exc)
            errors += 1
    logger.info("Sheet sync complete: %d synced, %d errors", synced, errors)
    return {"synced": synced, "errors": errors}


@shared_task(name="google_sheets.sync_single_cycle")
def sync_single_cycle(cycle_id: str):
    """Celery task: sync one specific cycle's sheet."""
    return SheetService.sync_cycle(cycle_id)

# pylint: disable=broad-except
"""
Migration bridge: sync MongoDB-generated alerts and tasks to Postgres.
Needed because monitoring_tasks.py writes to MongoDB (agent_model) while
the API reads from Postgres (pg_models) during the Phase 2 migration period.
"""

import logging
from datetime import datetime, timedelta

from celery import shared_task

logger = logging.getLogger("teramina")


@shared_task(name="agent.sync_mongo_alerts_to_pg")
def sync_mongo_alerts_to_pg():
    """
    Hourly: copy recent MongoDB FarmAlerts and WorkflowTasks to Postgres.
    Uses alert_type + cycle_id + created_at proximity as dedup key.
    """
    from teramina.agent.models.agent_model import (
        FarmAlert as MongoAlert,
        WorkflowTask as MongoTask,
    )
    from teramina.agent.models.pg_models import (
        FarmAlert as PgAlert,
        WorkflowTask as PgTask,
    )

    cutoff = datetime.utcnow() - timedelta(hours=25)
    synced_alerts = 0
    synced_tasks = 0

    # Sync alerts
    for alert in MongoAlert.objects(created_at__gte=cutoff):
        try:
            mongo_ref = f"mongo:{alert.id}"
            if not PgAlert.objects.filter(resolution_note=mongo_ref).exists():
                PgAlert.objects.create(
                    user_id=str(alert.user_id or ""),
                    farm_id=str(alert.farm_id or ""),
                    cycle_id=str(alert.cycle_id or ""),
                    alert_type=str(alert.alert_type or ""),
                    severity=str(alert.severity or "info"),
                    message=str(alert.message or ""),
                    data=alert.data or {},
                    is_read=bool(alert.is_read),
                    expires_at=alert.expires_at,
                    resolution_note=mongo_ref,  # used as idempotency key
                )
                synced_alerts += 1
        except Exception as exc:
            logger.warning("sync alert %s failed: %s", alert.id, exc)

    # Sync tasks
    for task in MongoTask.objects(created_at__gte=cutoff):
        try:
            mongo_ref = f"mongo:{task.id}"
            if not PgTask.objects.filter(source_alert_id=mongo_ref).exists():
                PgTask.objects.create(
                    user_id=str(task.user_id or ""),
                    farm_id=str(task.farm_id or ""),
                    cycle_id=str(task.cycle_id or ""),
                    task_type=str(task.task_type or "reminder"),
                    title=str(task.title or "")[:500],
                    description=str(task.description or ""),
                    due_at=task.due_at,
                    is_completed=bool(task.is_completed),
                    completed_at=task.completed_at,
                    source_alert_id=mongo_ref,
                )
                synced_tasks += 1
        except Exception as exc:
            logger.warning("sync task %s failed: %s", task.id, exc)

    logger.info("sync_mongo_alerts_to_pg: %d alerts, %d tasks synced", synced_alerts, synced_tasks)
    return {"synced_alerts": synced_alerts, "synced_tasks": synced_tasks}


@shared_task(name="agent.backfill_cycle_observations")
def backfill_cycle_observations(limit: int = 50):
    """
    Backfill CycleData.result_data rows into core_pg.CycleObservation.
    Run once per batch; call repeatedly with offset or let Celery Beat schedule it.
    """
    from teramina.cycle.models.cycle_model import Cycle
    from teramina.pond.models.pond_model import Pond
    from teramina.farm.models.farm_model import Farm
    from teramina.cycle_data.models.cycle_data_model import CycleData
    from teramina.core_pg.sync import sync_cycle_observations
    from teramina.core_pg.models import CycleObservation

    already_synced = set(
        CycleObservation.objects.values_list("cycle_id", flat=True).distinct()
    )

    cycles = Cycle.objects.all() if False else list(Cycle.objects())  # MongoEngine
    processed = 0
    total_rows = 0

    for cycle in cycles:
        if processed >= limit:
            break
        cycle_id = str(cycle.id)
        if cycle_id in already_synced:
            continue

        cd = CycleData.objects(cycle_id=cycle_id).first()
        if not cd or not cd.result_data:
            continue

        pond = Pond.objects(id=cycle.pond_id).first()
        if not pond:
            continue
        farm = Farm.objects(id=pond.farm_id).first()
        if not farm:
            continue

        n = sync_cycle_observations(
            cycle_id=cycle_id,
            pond_id=str(pond.id),
            farm_id=str(farm.id),
            user_id=str(farm.user_id),
            result_data=cd.result_data,
        )
        total_rows += n
        processed += 1

    logger.info("backfill_cycle_observations: %d cycles, %d rows synced", processed, total_rows)
    return {"cycles_processed": processed, "rows_synced": total_rows}

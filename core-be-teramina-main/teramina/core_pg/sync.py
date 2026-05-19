# pylint: disable=broad-except
"""
Dual-write sync helpers — called alongside MongoEngine saves during Phase 2 migration.
Each function is safe to call from services: exceptions are caught and logged, never fatal.
"""

import logging
from datetime import datetime

logger = logging.getLogger("teramina")


def sync_farm(mongo_farm) -> None:
    try:
        from teramina.core_pg.models import Farm
        Farm.objects.update_or_create(
            mongo_id=str(mongo_farm.id),
            defaults={
                "user_id": str(mongo_farm.user_id or ""),
                "name": mongo_farm.name or "",
                "location": mongo_farm.location or "",
            },
        )
    except Exception as exc:
        logger.warning("sync_farm failed for %s: %s", mongo_farm.id, exc)


def sync_pond(mongo_pond) -> None:
    try:
        from teramina.core_pg.models import Pond
        Pond.objects.update_or_create(
            mongo_id=str(mongo_pond.id),
            defaults={
                "farm_id": str(mongo_pond.farm_id or ""),
                "user_id": "",  # resolved at backfill time
                "name": mongo_pond.name or "",
                "size": mongo_pond.size,
                "depth": mongo_pond.depth or 1.5,
                "pond_construction": mongo_pond.pond_construction or "",
                "pond_shape": mongo_pond.pond_shape or "",
                "is_active": bool(mongo_pond.is_active),
                "active_cycle_id": str(mongo_pond.active_cycle_id or ""),
            },
        )
    except Exception as exc:
        logger.warning("sync_pond failed for %s: %s", mongo_pond.id, exc)


def sync_cycle(mongo_cycle, farm_id="", user_id="") -> None:
    try:
        from teramina.core_pg.models import Cycle
        Cycle.objects.update_or_create(
            mongo_id=str(mongo_cycle.id),
            defaults={
                "pond_id": str(mongo_cycle.pond_id or ""),
                "farm_id": farm_id,
                "user_id": user_id,
                "name": mongo_cycle.name or "",
                "start_date": mongo_cycle.start_date,
                "end_date": None,
                "is_active": bool(mongo_cycle.is_active),
            },
        )
    except Exception as exc:
        logger.warning("sync_cycle failed for %s: %s", mongo_cycle.id, exc)


def sync_cycle_observations(cycle_id: str, pond_id: str, farm_id: str, user_id: str, result_data: list) -> int:
    """Upsert structured daily observations from CycleData.result_data rows."""
    if not result_data:
        return 0
    try:
        from teramina.core_pg.models import CycleObservation
        synced = 0
        for row in result_data:
            doc = row.get("doc")
            if doc is None:
                continue
            CycleObservation.objects.update_or_create(
                cycle_id=cycle_id,
                doc=doc,
                defaults={
                    "pond_id": pond_id,
                    "farm_id": farm_id,
                    "user_id": user_id,
                    "recorded_at": datetime.utcnow(),
                    "do_avg": row.get("do_avg"),
                    "temp_avg": row.get("temp") or row.get("temp_avg"),
                    "nh3": row.get("nh3"),
                    "salinity": row.get("salinity"),
                    "ph": row.get("ph"),
                    "turbidity": row.get("turbidity"),
                    "abw": row.get("abw"),
                    "biomass": row.get("biomass") or row.get("pond_biomass"),
                    "survival_rate": row.get("survival_rate") or row.get("sr"),
                    "sgr": row.get("sgr"),
                    "fcr": row.get("fcr"),
                    "source": "backfill",
                    "formula_version": row.get("formula_version", ""),
                    "raw_data": row,
                },
            )
            synced += 1
        return synced
    except Exception as exc:
        logger.warning("sync_cycle_observations failed for cycle %s: %s", cycle_id, exc)
        return 0


def sync_feed_event(mongo_feed, pond_id="", farm_id="", user_id="") -> None:
    try:
        from teramina.core_pg.models import FeedEvent
        FeedEvent.objects.update_or_create(
            cycle_id=str(mongo_feed.cycle_id or ""),
            doc=mongo_feed.doc or 0,
            ration_number=mongo_feed.ration_number or 1,
            defaults={
                "pond_id": pond_id,
                "farm_id": farm_id,
                "user_id": user_id,
                "feed_ration": mongo_feed.feed_ration,
                "feed_given": mongo_feed.feed_given,
                "feed_leftover": mongo_feed.feed_leftover,
                "recorded_at": mongo_feed.last_updated or datetime.utcnow(),
            },
        )
    except Exception as exc:
        logger.warning("sync_feed_event failed: %s", exc)


def sync_harvest_record(mongo_harvest, pond_id="", farm_id="", user_id="") -> None:
    try:
        from teramina.core_pg.models import HarvestEvent
        harvest_data = mongo_harvest.harvest_data or {}
        HarvestEvent.objects.update_or_create(
            cycle_id=str(mongo_harvest.cycle_id or ""),
            harvest_date=mongo_harvest.last_updated or datetime.utcnow(),
            defaults={
                "pond_id": pond_id,
                "farm_id": farm_id,
                "user_id": user_id,
                "harvest_type": harvest_data.get("harvest_type", "partial"),
                "doc": harvest_data.get("doc"),
                "weight_kg": harvest_data.get("weight_kg") or harvest_data.get("total_weight"),
                "size_count": harvest_data.get("size") or harvest_data.get("count_per_kg"),
                "price_per_kg_idr": harvest_data.get("price_per_kg"),
                "revenue_idr": harvest_data.get("revenue") or harvest_data.get("total_revenue"),
                "notes": harvest_data.get("notes", ""),
                "raw_data": harvest_data,
            },
        )
    except Exception as exc:
        logger.warning("sync_harvest_record failed: %s", exc)

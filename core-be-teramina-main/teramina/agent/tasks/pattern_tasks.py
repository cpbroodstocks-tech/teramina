# pylint: disable=broad-except
"""
Phase 5 — Pattern Detection Jobs.
Celery Beat tasks that scan historical cycle data to detect recurring patterns
and store them as graph memory (MemoryEntity + MemoryRelation + AgentMemory).
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta

from celery import shared_task

from teramina.cycle.models.cycle_model import Cycle
from teramina.pond.models.pond_model import Pond
from teramina.farm.models.farm_model import Farm
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.cost_data.models.cost_data_model import CostData
from teramina.helpers.constant_value import Constant

from teramina.agent.models.agent_model import AgentMemory, MemoryEntity, MemoryRelation
from teramina.agent.services.memory_retrieval import index_agent_memory

logger = logging.getLogger("teramina")


# ── Helpers ─────────────────────────────────────────────────────────────────


def _get_or_create_entity(user_id, farm_id, entity_type, canonical_name, metadata=None):
    entity = MemoryEntity.objects(
        user_id=user_id,
        farm_id=farm_id,
        entity_type=entity_type,
        canonical_name=canonical_name,
    ).first()
    if not entity:
        entity = MemoryEntity(
            user_id=user_id,
            farm_id=farm_id,
            entity_type=entity_type,
            canonical_name=canonical_name,
            metadata=metadata or {},
        ).save()
    return entity


def _ensure_relation(user_id, farm_id, source_id, relation_type, target_id, confidence=0.75):
    existing = MemoryRelation.objects(
        user_id=user_id,
        farm_id=farm_id,
        source_entity_id=str(source_id),
        relation_type=relation_type,
        target_entity_id=str(target_id),
    ).first()
    if not existing:
        MemoryRelation(
            user_id=user_id,
            farm_id=farm_id,
            source_entity_id=str(source_id),
            relation_type=relation_type,
            target_entity_id=str(target_id),
            confidence=confidence,
            source_type="ai_inference",
        ).save()


def _store_pattern_memory(user_id, farm_id, pond_id, cycle_id, content, tags):
    try:
        mem = AgentMemory(
            user_id=user_id,
            farm_id=farm_id,
            pond_id=pond_id,
            cycle_id=cycle_id,
            memory_type="event",
            content=content,
            tags=tags,
            source="system_observation",
            confidence=0.75,
            is_verified=False,
        ).save()
        index_agent_memory(mem)
    except Exception as exc:
        logger.warning("_store_pattern_memory failed: %s", exc)


def _get_cycle_context(cycle):
    """Resolve pond and farm for a Cycle. Returns (pond, farm) or (None, None)."""
    pond = Pond.objects(id=cycle.pond_id).first()
    if not pond:
        return None, None
    farm = Farm.objects(id=pond.farm_id).first()
    return pond, farm


# ── Task 1: Low DO Patterns ──────────────────────────────────────────────────


@shared_task(name="agent.detect_recurring_low_do_patterns")
def detect_recurring_low_do_patterns():
    """
    Per pond: collect DO readings across all cycles.
    If DO < optimal in ≥50% of cycles AND at a consistent DOC range → store pattern.
    """
    ponds = Pond.objects(is_active=True)
    detected = 0

    for pond in ponds:
        try:
            pond_id = str(pond.id)
            farm = Farm.objects(id=pond.farm_id).first()
            if not farm:
                continue
            farm_id = str(farm.id)
            user_id = str(farm.user_id)

            cycles = list(Cycle.objects(pond_id=pond_id))
            if len(cycles) < 2:
                continue

            low_do_cycles = []
            low_do_doc_ranges = []

            for cycle in cycles:
                cd = CycleData.objects(cycle_id=str(cycle.id)).first()
                if not cd or not cd.result_data:
                    continue
                do_rows = sorted(
                    [(r["doc"], r["do_avg"]) for r in cd.result_data if r.get("doc") and r.get("do_avg")],
                    key=lambda x: x[0],
                )
                if not do_rows:
                    continue
                low_docs = [doc for doc, do_val in do_rows if do_val < Constant.DO_OPTIMAL_MIN]
                if low_docs:
                    low_do_cycles.append(str(cycle.id))
                    low_do_doc_ranges.extend(low_docs)

            if len(low_do_cycles) / max(len(cycles), 1) >= 0.5 and low_do_doc_ranges:
                avg_doc = sum(low_do_doc_ranges) / len(low_do_doc_ranges)
                pattern_name = f"low_DO_around_DOC_{int(avg_doc)}"

                pond_entity = _get_or_create_entity(user_id, farm_id, "pond", pond.name or pond_id)
                pattern_entity = _get_or_create_entity(
                    user_id, farm_id, "issue", pattern_name,
                    {"avg_doc": int(avg_doc), "affected_cycles": len(low_do_cycles)},
                )
                _ensure_relation(user_id, farm_id, pond_entity.id, "observed", pattern_entity.id, confidence=0.8)

                _store_pattern_memory(
                    user_id, farm_id, pond_id, "",
                    f"Recurring low DO detected in pond {pond.name or pond_id}: "
                    f"low DO in {len(low_do_cycles)}/{len(cycles)} cycles, typically around DOC {int(avg_doc)}.",
                    ["water_quality", "do", "recurring_pattern"],
                )
                detected += 1

        except Exception as exc:
            logger.error("detect_recurring_low_do_patterns error for pond %s: %s", pond.id, exc)

    logger.info("detect_recurring_low_do_patterns: %d patterns stored", detected)
    return {"detected": detected}


# ── Task 2: Growth Lag Patterns ───────────────────────────────────────────────


@shared_task(name="agent.detect_growth_lag_patterns")
def detect_growth_lag_patterns():
    """
    Per pond: detect if SGR consistently drops below 3.5%/day after DOC 45
    across multiple cycles → store growth_lag pattern.
    """
    ponds = Pond.objects(is_active=True)
    detected = 0

    for pond in ponds:
        try:
            pond_id = str(pond.id)
            farm = Farm.objects(id=pond.farm_id).first()
            if not farm:
                continue
            farm_id = str(farm.id)
            user_id = str(farm.user_id)

            cycles = list(Cycle.objects(pond_id=pond_id))
            if len(cycles) < 2:
                continue

            lag_cycles = 0
            for cycle in cycles:
                cd = CycleData.objects(cycle_id=str(cycle.id)).first()
                if not cd or not cd.result_data:
                    continue
                abw_rows = sorted(
                    [(r["doc"], r["abw"]) for r in cd.result_data
                     if r.get("doc") and r.get("abw") and r["doc"] > 45],
                    key=lambda x: x[0],
                )
                if len(abw_rows) < 2:
                    continue
                d1, w1 = abw_rows[-2]
                d2, w2 = abw_rows[-1]
                if w1 > 0 and w2 > 0 and d2 > d1:
                    sgr = (math.log(w2) - math.log(w1)) / (d2 - d1) * 100
                    if sgr < 3.5:
                        lag_cycles += 1

            if lag_cycles / max(len(cycles), 1) >= 0.5:
                pond_entity = _get_or_create_entity(user_id, farm_id, "pond", pond.name or pond_id)
                pattern_entity = _get_or_create_entity(
                    user_id, farm_id, "issue", "growth_lag_after_DOC_45",
                    {"affected_cycles": lag_cycles},
                )
                _ensure_relation(user_id, farm_id, pond_entity.id, "observed", pattern_entity.id, confidence=0.75)

                _store_pattern_memory(
                    user_id, farm_id, pond_id, "",
                    f"Recurring growth lag detected in pond {pond.name or pond_id}: "
                    f"SGR < 3.5%/day after DOC 45 in {lag_cycles}/{len(cycles)} cycles.",
                    ["growth", "sgr", "recurring_pattern"],
                )
                detected += 1

        except Exception as exc:
            logger.error("detect_growth_lag_patterns error for pond %s: %s", pond.id, exc)

    logger.info("detect_growth_lag_patterns: %d patterns stored", detected)
    return {"detected": detected}


# ── Task 3: High Feed Leftover Patterns ──────────────────────────────────────


@shared_task(name="agent.detect_high_feed_leftover_patterns")
def detect_high_feed_leftover_patterns():
    """
    Per pond: if feed leftover rate > 20% persists across ≥2 cycles → pattern.
    """
    ponds = Pond.objects(is_active=True)
    detected = 0

    for pond in ponds:
        try:
            pond_id = str(pond.id)
            farm = Farm.objects(id=pond.farm_id).first()
            if not farm:
                continue
            farm_id = str(farm.id)
            user_id = str(farm.user_id)

            cycles = list(Cycle.objects(pond_id=pond_id))
            if len(cycles) < 2:
                continue

            high_leftover_cycles = 0
            for cycle in cycles:
                feed_records = list(FeedRealization.objects(cycle_id=str(cycle.id)))
                if not feed_records:
                    continue
                total_given = sum(r.feed_given or 0 for r in feed_records)
                total_leftover = sum(r.feed_leftover or 0 for r in feed_records)
                if total_given > 0 and (total_leftover / total_given) > 0.20:
                    high_leftover_cycles += 1

            if high_leftover_cycles >= 2:
                pond_entity = _get_or_create_entity(user_id, farm_id, "pond", pond.name or pond_id)
                pattern_entity = _get_or_create_entity(
                    user_id, farm_id, "issue", "high_feed_leftover",
                    {"affected_cycles": high_leftover_cycles},
                )
                _ensure_relation(user_id, farm_id, pond_entity.id, "observed", pattern_entity.id, confidence=0.75)

                _store_pattern_memory(
                    user_id, farm_id, pond_id, "",
                    f"Recurring high feed leftover in pond {pond.name or pond_id}: "
                    f">20% leftover in {high_leftover_cycles}/{len(cycles)} cycles. "
                    "Consider reviewing feed ration sizing.",
                    ["feeding", "fcr", "recurring_pattern"],
                )
                detected += 1

        except Exception as exc:
            logger.error("detect_high_feed_leftover_patterns error for pond %s: %s", pond.id, exc)

    logger.info("detect_high_feed_leftover_patterns: %d patterns stored", detected)
    return {"detected": detected}


# ── Task 4: Harvest Outcome Patterns ─────────────────────────────────────────


@shared_task(name="agent.detect_harvest_outcome_patterns")
def detect_harvest_outcome_patterns():
    """
    Per pond: collect harvest outcomes (size, weight, price) across cycles.
    Store best-cycle outcome and average as memory for harvest planning context.
    """
    ponds = Pond.objects(is_active=True)
    detected = 0

    for pond in ponds:
        try:
            pond_id = str(pond.id)
            farm = Farm.objects(id=pond.farm_id).first()
            if not farm:
                continue
            farm_id = str(farm.id)
            user_id = str(farm.user_id)

            cycles = list(Cycle.objects(pond_id=pond_id))
            if not cycles:
                continue

            outcomes = []
            for cycle in cycles:
                harvest = HarvestRecord.objects(cycle_id=str(cycle.id)).first()
                if not harvest or not harvest.harvest_data:
                    continue
                hd = harvest.harvest_data
                weight = hd.get("weight_kg") or hd.get("total_weight")
                size = hd.get("size") or hd.get("count_per_kg")
                price = hd.get("price_per_kg")
                if weight:
                    outcomes.append({
                        "cycle_id": str(cycle.id),
                        "weight_kg": weight,
                        "size": size,
                        "price_per_kg_idr": price,
                    })

            if len(outcomes) >= 2:
                avg_weight = sum(o["weight_kg"] for o in outcomes) / len(outcomes)
                best = max(outcomes, key=lambda o: o["weight_kg"])

                pond_entity = _get_or_create_entity(user_id, farm_id, "pond", pond.name or pond_id)
                outcome_entity = _get_or_create_entity(
                    user_id, farm_id, "event", f"harvest_outcomes_{pond_id[:8]}",
                    {"avg_weight_kg": round(avg_weight, 1), "best_weight_kg": best["weight_kg"],
                     "sample_cycles": len(outcomes)},
                )
                _ensure_relation(user_id, farm_id, pond_entity.id, "resulted_in", outcome_entity.id, confidence=0.8)

                size_str = f", avg size {outcomes[0]['size']} count/kg" if outcomes[0].get("size") else ""
                _store_pattern_memory(
                    user_id, farm_id, pond_id, "",
                    f"Harvest history for pond {pond.name or pond_id}: "
                    f"avg yield {avg_weight:.1f} kg over {len(outcomes)} cycles{size_str}. "
                    f"Best cycle: {best['weight_kg']:.1f} kg.",
                    ["harvest", "outcome", "pattern"],
                )
                detected += 1

        except Exception as exc:
            logger.error("detect_harvest_outcome_patterns error for pond %s: %s", pond.id, exc)

    logger.info("detect_harvest_outcome_patterns: %d patterns stored", detected)
    return {"detected": detected}


# ── Task 5: Cost Overrun Patterns ────────────────────────────────────────────


@shared_task(name="agent.detect_cost_overrun_patterns")
def detect_cost_overrun_patterns():
    """
    Per farm: compare cost/kg across cycles. If consistently >20% above 25,000 IDR/kg → pattern.
    """
    farms = Farm.objects()
    detected = 0

    for farm in farms:
        try:
            farm_id = str(farm.id)
            user_id = str(farm.user_id)

            cost_doc = CostData.objects(farm_id=farm_id).first()
            if not cost_doc or not cost_doc.data:
                continue

            total_cost = sum(r.get("total", 0) or 0 for r in cost_doc.data)
            if total_cost <= 0:
                continue

            active_cycles = list(Cycle.objects(is_active=True))
            farm_cycle_ids = []
            for cycle in active_cycles:
                pond = Pond.objects(id=cycle.pond_id).first()
                if pond and str(pond.farm_id) == farm_id:
                    farm_cycle_ids.append(str(cycle.id))

            if not farm_cycle_ids:
                continue

            biomass_estimates = []
            for cycle_id in farm_cycle_ids:
                cd = CycleData.objects(cycle_id=cycle_id).first()
                if not cd or not cd.result_data:
                    continue
                biomass_rows = [
                    (r["doc"], r.get("biomass") or r.get("pond_biomass"))
                    for r in cd.result_data if r.get("doc") and (r.get("biomass") or r.get("pond_biomass"))
                ]
                if biomass_rows:
                    latest = sorted(biomass_rows, key=lambda x: x[0])[-1][1]
                    if latest and latest > 0:
                        biomass_estimates.append(latest)

            if not biomass_estimates:
                continue

            total_biomass = sum(biomass_estimates)
            cost_per_kg = total_cost / total_biomass
            benchmark = 25_000

            if cost_per_kg > benchmark * 1.2:
                farm_entity = _get_or_create_entity(user_id, farm_id, "farm", farm.name or farm_id)
                pattern_entity = _get_or_create_entity(
                    user_id, farm_id, "issue", "cost_overrun",
                    {"cost_per_kg_idr": round(cost_per_kg), "benchmark_idr": benchmark},
                )
                _ensure_relation(user_id, farm_id, farm_entity.id, "observed", pattern_entity.id, confidence=0.7)

                _store_pattern_memory(
                    user_id, farm_id, "", "",
                    f"Cost overrun pattern for farm {farm.name or farm_id}: "
                    f"Rp{cost_per_kg:,.0f}/kg vs benchmark Rp{benchmark:,}/kg "
                    f"({((cost_per_kg / benchmark) - 1) * 100:.0f}% above target). "
                    "Review feed and operational costs.",
                    ["cost", "overrun", "recurring_pattern"],
                )
                detected += 1

        except Exception as exc:
            logger.error("detect_cost_overrun_patterns error for farm %s: %s", farm.id, exc)

    logger.info("detect_cost_overrun_patterns: %d patterns stored", detected)
    return {"detected": detected}


# ── Orchestrator: run all pattern jobs ───────────────────────────────────────


@shared_task(name="agent.detect_all_patterns")
def detect_all_patterns():
    """Weekly orchestrator: run all 5 pattern detection jobs in sequence."""
    results = {}
    for task_fn in [
        detect_recurring_low_do_patterns,
        detect_growth_lag_patterns,
        detect_high_feed_leftover_patterns,
        detect_harvest_outcome_patterns,
        detect_cost_overrun_patterns,
    ]:
        try:
            result = task_fn()
            results[task_fn.name] = result
        except Exception as exc:
            logger.error("Pattern task %s failed: %s", task_fn.name, exc)
            results[task_fn.name] = {"error": str(exc)}
    logger.info("detect_all_patterns complete: %s", results)
    return results

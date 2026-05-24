# pylint: disable=broad-except

"""
Tool implementations for the farm assistant agent.
Each function corresponds to one Claude tool call.
"""

import logging
import math
from datetime import datetime, timedelta
from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData
from teramina.cost_data.models.cost_data_model import CostData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.helpers.constant_value import Constant
from teramina.agent.models.agent_model import (
    AgentMemory,
    FarmAlert,
    MemoryEntity,
    MemoryObservation,
    MemoryRelation,
    WorkflowTask,
)

logger = logging.getLogger("teramina")


def _get_or_create_memory_entity(user_id: str, farm_id: str, entity_type: str,
                                 canonical_name: str, metadata: dict | None = None) -> MemoryEntity:
    """Return an existing graph entity or create it."""
    entity = MemoryEntity.objects.filter(
        user_id=user_id,
        farm_id=farm_id or "",
        entity_type=entity_type,
        canonical_name=canonical_name,
    ).first()
    if entity:
        if metadata:
            entity.metadata = {**(entity.metadata or {}), **metadata}
            entity.save()
        return entity
    return MemoryEntity.objects.create(
        user_id=user_id,
        farm_id=farm_id or "",
        entity_type=entity_type,
        canonical_name=canonical_name,
        metadata=metadata or {},
    )


def _link_memory_entities(user_id: str, farm_id: str, source_id: str,
                          relation_type: str, target_id: str,
                          source_type: str = "ai_inference") -> None:
    """Create a graph relation if it does not already exist."""
    if MemoryRelation.objects(
        user_id=user_id,
        farm_id=farm_id or "",
        source_entity_id=source_id,
        relation_type=relation_type,
        target_entity_id=target_id,
    ).first():
        return
    MemoryRelation.objects.create(
        user_id=user_id,
        farm_id=farm_id or "",
        source_entity_id=source_id,
        relation_type=relation_type,
        target_entity_id=target_id,
        source_type=source_type,
    )


def _store_memory_observation(user_id: str, farm_id: str, memory_type: str, content: str,
                              pond_id: str = "", cycle_id: str = "", source_type: str = "ai_inference",
                              is_verified: bool = False, source_ref: str = "") -> MemoryObservation:
    """Store graph observation and connect it to farm/pond/cycle entities."""
    farm_entity = _get_or_create_memory_entity(user_id, farm_id, "farm", farm_id or "farm")
    target_entity = farm_entity
    if pond_id:
        pond_entity = _get_or_create_memory_entity(user_id, farm_id, "pond", pond_id)
        _link_memory_entities(user_id, farm_id, str(farm_entity.id), "contains", str(pond_entity.id), source_type)
        target_entity = pond_entity
    if cycle_id:
        cycle_entity = _get_or_create_memory_entity(user_id, farm_id, "cycle", cycle_id)
        _link_memory_entities(user_id, farm_id, str(target_entity.id), "contains", str(cycle_entity.id), source_type)
        target_entity = cycle_entity

    observation_type = {
        "fact": "fact",
        "preference": "preference",
        "event": "event_summary",
        "advice": "action_summary",
        "note": "note",
    }.get(memory_type, "note")

    return MemoryObservation.objects.create(
        user_id=user_id,
        farm_id=farm_id or "",
        pond_id=pond_id or "",
        cycle_id=cycle_id or "",
        entity_id=str(target_entity.id),
        observation_type=observation_type,
        content=content,
        source_type=source_type,
        source_ref=source_ref or "",
        is_verified=is_verified,
    )


def get_farm_overview(farm_id: str) -> dict:
    """Return farm info, all ponds, and active cycles with latest metrics."""
    farm = Farm.objects(id=farm_id).first()
    if not farm:
        return {"error": f"Farm {farm_id} not found"}

    ponds = Pond.objects(farm_id=farm_id)
    result = {
        "farm_name": farm.name,
        "farm_location": farm.location,
        "ponds": [],
    }
    for pond in ponds:
        pond_entry = {
            "pond_id": str(pond.id),
            "pond_name": pond.name,
            "is_active": pond.is_active,
            "active_cycle_id": pond.active_cycle_id or None,
            "current_doc": None,
            "latest_abw_g": None,
            "do_avg_3d": None,
        }
        if pond.active_cycle_id:
            cd = CycleData.objects(cycle_id=pond.active_cycle_id).first()
            if cd and cd.result_data:
                rows = sorted(
                    [r for r in cd.result_data if r.get("doc")],
                    key=lambda x: x["doc"],
                )
                if rows:
                    latest = rows[-1]
                    pond_entry["current_doc"] = latest.get("doc")
                    pond_entry["latest_abw_g"] = latest.get("abw")
                    recent_do = [r.get("do_avg") for r in rows[-3:] if r.get("do_avg")]
                    if recent_do:
                        pond_entry["do_avg_3d"] = round(sum(recent_do) / len(recent_do), 2)
        result["ponds"].append(pond_entry)
    return result


def get_cycle_metrics(cycle_id: str) -> dict:
    """Return current performance metrics for a cycle."""
    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return {"error": f"Cycle {cycle_id} not found"}

    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No cycle data available", "cycle_id": cycle_id}

    rows = sorted([r for r in cd.result_data if r.get("doc")], key=lambda x: x["doc"])
    if not rows:
        return {"error": "No DOC data in cycle", "cycle_id": cycle_id}

    latest = rows[-1]
    recent = rows[-7:]
    do_vals = [r.get("do_avg") for r in recent if r.get("do_avg")]
    nh3_vals = [r.get("nh3") for r in recent if r.get("nh3")]
    temp_vals = [r.get("temp_avg") for r in recent if r.get("temp_avg")]

    return {
        "cycle_id": cycle_id,
        "cycle_name": cycle.name,
        "current_doc": latest.get("doc"),
        "latest_abw_g": latest.get("abw"),
        "do_avg_7d": round(sum(do_vals) / len(do_vals), 2) if do_vals else None,
        "nh3_avg_7d": round(sum(nh3_vals) / len(nh3_vals), 3) if nh3_vals else None,
        "temp_avg_7d": round(sum(temp_vals) / len(temp_vals), 1) if temp_vals else None,
        "status": cycle.status if hasattr(cycle, "status") else "active",
    }


def get_water_quality_trend(cycle_id: str, days: int = 7) -> dict:
    """Return water quality readings over the last N days."""
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No water quality data", "cycle_id": cycle_id}

    rows = sorted([r for r in cd.result_data if r.get("doc")], key=lambda x: x["doc"])
    recent = rows[-days:] if len(rows) >= days else rows
    readings = [
        {
            "doc": r.get("doc"),
            "do_avg": r.get("do_avg"),
            "temp_avg": r.get("temp_avg"),
            "nh3": r.get("nh3"),
            "ph": r.get("ph"),
            "salinity": r.get("salinity"),
        }
        for r in recent
    ]
    return {"cycle_id": cycle_id, "days": days, "readings": readings}


def get_forecast(cycle_id: str) -> dict:
    """Return optimal harvest DOC, projected biomass and profit."""
    fd = ForecastData.objects(cycle_id=cycle_id).first()
    if not fd or not fd.result_data:
        return {"error": "No forecast data", "cycle_id": cycle_id}

    best_profit = float("-inf")
    best_row = None
    for row in fd.result_data:
        profit = row.get("profit") or row.get("forecasted_profit") or 0
        if profit > best_profit:
            best_profit = profit
            best_row = row

    if not best_row:
        return {"error": "No valid forecast rows", "cycle_id": cycle_id}

    return {
        "cycle_id": cycle_id,
        "optimal_doc": best_row.get("doc"),
        "projected_abw_g": best_row.get("abw") or best_row.get("adj_abw"),
        "projected_biomass_kg": best_row.get("biomass") or best_row.get("pond_biomass"),
        "projected_profit_idr": round(best_profit, 0),
    }


def get_cost_breakdown(cycle_id: str) -> dict:
    """Return total cost and breakdown by category for a cycle."""
    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return {"error": f"Cycle {cycle_id} not found"}
    cost_doc = CostData.objects(cycle_id=cycle_id).first()
    if not cost_doc or not cost_doc.data:
        return {"error": "No cost data", "cycle_id": cycle_id}

    total = 0
    breakdown = {}
    for row in cost_doc.data:
        category = row.get("category", "other")
        amount = row.get("total", 0) or 0
        total += amount
        breakdown[category] = breakdown.get(category, 0) + amount

    return {
        "cycle_id": cycle_id,
        "total_idr": round(total, 0),
        "breakdown": {k: round(v, 0) for k, v in breakdown.items()},
    }


def get_growth_trend(cycle_id: str, days: int = 14) -> dict:
    """Return ABW progression and SGR over the last N days."""
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No cycle data", "cycle_id": cycle_id}

    abw_rows = sorted(
        [(r["doc"], r["abw"]) for r in cd.result_data if r.get("abw") and r.get("doc")],
        key=lambda x: x[0],
    )
    recent = abw_rows[-days:] if len(abw_rows) >= days else abw_rows
    if len(recent) < 2:
        return {"error": "Not enough ABW data points", "cycle_id": cycle_id}

    d1, w1 = recent[-2]
    d2, w2 = recent[-1]
    sgr = (math.log(w2) - math.log(w1)) / (d2 - d1) * 100 if w1 > 0 and w2 > 0 and d2 > d1 else None

    all_sgrs = []
    for i in range(1, len(recent)):
        da, wa = recent[i - 1]
        db, wb = recent[i]
        if wa > 0 and wb > 0 and db > da:
            all_sgrs.append((math.log(wb) - math.log(wa)) / (db - da) * 100)

    return {
        "cycle_id": cycle_id,
        "abw_series": [{"doc": d, "abw_g": w} for d, w in recent],
        "current_sgr_pct_day": round(sgr, 3) if sgr is not None else None,
        "avg_sgr_pct_day": round(sum(all_sgrs) / len(all_sgrs), 3) if all_sgrs else None,
        "expected_sgr_pct_day": 3.5,
        "growth_status": "lagging" if sgr and sgr < 3.5 else "normal",
    }


def get_feeding_summary(cycle_id: str, days: int = 7) -> dict:
    """Return feeding summary: total feed, leftover rate, and feeding status."""
    recent_feed = list(FeedRealization.objects(cycle_id=cycle_id).order_by("-doc").limit(days))
    if not recent_feed:
        return {"error": "No feeding data", "cycle_id": cycle_id}

    total_given = sum(r.feed_given or 0 for r in recent_feed)
    total_leftover = sum(r.feed_leftover or 0 for r in recent_feed)
    leftover_pct = (total_leftover / total_given * 100) if total_given > 0 else 0

    return {
        "cycle_id": cycle_id,
        "days": days,
        "total_feed_kg": round(total_given, 2),
        "leftover_pct": round(leftover_pct, 1),
        "feeding_status": "overfeeding" if leftover_pct > 20 else "normal",
    }


def get_cycle_timeline(cycle_id: str, limit: int = 20) -> dict:
    """Return chronological event timeline for a cycle."""
    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return {"error": f"Cycle {cycle_id} not found"}

    events = []

    cd = CycleData.objects(cycle_id=cycle_id).first()
    if cd and cd.result_data:
        for r in cd.result_data:
            doc = r.get("doc")
            if not doc:
                continue
            notes = []
            do_val = r.get("do_avg")
            nh3_val = r.get("nh3")
            if do_val and do_val < Constant.DO_SUITABLE_MIN:
                notes.append(f"DO critical: {do_val}")
            elif do_val and do_val < Constant.DO_OPTIMAL_MIN:
                notes.append(f"DO below optimal: {do_val}")
            if nh3_val and nh3_val > Constant.NH3_SUITABLE_MAX * 0.8:
                notes.append(f"NH3 high: {nh3_val}")
            if notes:
                events.append({
                    "type": "observation",
                    "doc": doc,
                    "date": None,
                    "description": "; ".join(notes),
                })

    for alert in FarmAlert.objects.filter(cycle_id=cycle_id).order_by("created_at")[:50]:
        events.append({
            "type": "alert",
            "doc": None,
            "date": alert.created_at.isoformat() if alert.created_at else None,
            "severity": alert.severity,
            "description": alert.message,
        })

    for mem in AgentMemory.objects.filter(cycle_id=cycle_id).order_by("created_at")[:20]:
        events.append({
            "type": f"memory_{mem.memory_type}",
            "doc": None,
            "date": mem.created_at.isoformat() if mem.created_at else None,
            "description": mem.content,
            "tags": mem.tags,
        })

    events.sort(key=lambda e: (e.get("doc") or 9999, e.get("date") or ""))

    return {
        "cycle_id": cycle_id,
        "cycle_name": cycle.name,
        "start_date": cycle.start_date.isoformat() if cycle.start_date else None,
        "total_events": len(events),
        "events": events[-limit:],
    }


def create_reminder(farm_id: str, title: str, due_in_hours: int,
                    description: str = "", pond_id: str = "", cycle_id: str = "",
                    task_type: str = "reminder") -> dict:
    """Create a follow-up task or reminder for the farmer."""
    farm = Farm.objects(id=farm_id).first()
    if not farm:
        return {"error": f"Farm {farm_id} not found"}
    valid_types = {"reminder", "follow_up", "check", "action"}
    if task_type not in valid_types:
        task_type = "reminder"
    due_at = datetime.utcnow() + timedelta(hours=due_in_hours)
    task = WorkflowTask.objects.create(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id or "",
        cycle_id=cycle_id or "",
        task_type=task_type,
        title=title,
        description=description,
        due_at=due_at,
    )
    return {
        "created": True,
        "task_id": str(task.id),
        "title": title,
        "due_at": due_at.isoformat(),
    }


def compare_scenarios(cycle_id: str, harvest_docs: list) -> dict:
    """Compare profit/yield projections for different harvest DOC scenarios."""
    fd = ForecastData.objects(cycle_id=cycle_id).first()
    if not fd or not fd.result_data:
        return {"error": "No forecast data available", "cycle_id": cycle_id}

    forecast_by_doc = {}
    for row in fd.result_data:
        doc = row.get("doc")
        if doc is not None:
            forecast_by_doc[doc] = row

    if not forecast_by_doc:
        return {"error": "Forecast rows have no DOC field", "cycle_id": cycle_id}

    scenarios = []
    for target_doc in harvest_docs:
        closest = min(forecast_by_doc.keys(), key=lambda d: abs(d - target_doc))
        row = forecast_by_doc[closest]
        profit = row.get("profit") or row.get("forecasted_profit") or 0
        scenarios.append({
            "target_doc": target_doc,
            "actual_doc": closest,
            "projected_abw_g": row.get("abw") or row.get("adj_abw"),
            "projected_biomass_kg": row.get("biomass") or row.get("pond_biomass"),
            "projected_profit_idr": round(profit, 0),
        })

    best = max(scenarios, key=lambda s: s["projected_profit_idr"] or 0)
    for s in scenarios:
        s["is_optimal"] = (s["actual_doc"] == best["actual_doc"])

    return {
        "cycle_id": cycle_id,
        "scenarios": scenarios,
        "optimal_doc": best["actual_doc"],
        "recommendation": f"DOC {best['actual_doc']} yields the highest projected profit",
    }


def log_farmer_action(farm_id: str, action_description: str, outcome: str = "",
                      pond_id: str = "", cycle_id: str = "") -> dict:
    """Record a confirmed farmer action and its outcome as a verified advice memory."""
    from .memory_retrieval import index_agent_memory, index_memory_observation
    farm = Farm.objects(id=farm_id).first()
    if not farm:
        return {"error": f"Farm {farm_id} not found"}
    content = f"Action: {action_description}"
    if outcome:
        content += f" | Outcome: {outcome}"
    memory = AgentMemory.objects.create(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id or "",
        cycle_id=cycle_id or "",
        memory_type="advice",
        content=content,
        tags=["action", "confirmed"],
        source="user_input",
        is_verified=True,
    )
    index_agent_memory(memory)
    observation = _store_memory_observation(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id,
        cycle_id=cycle_id,
        memory_type="advice",
        content=content,
        source_type="farmer",
        is_verified=True,
        source_ref=f"agent_memory:{memory.id}",
    )
    index_memory_observation(observation)
    return {"logged": True, "content": content}


def search_farm_memory(farm_id: str, query: str = "", pond_id: str = "", limit: int = 10) -> dict:
    """Search durable farmer memories for relevant context."""
    from .memory_retrieval import semantic_search_memories

    return semantic_search_memories(farm_id, query=query, pond_id=pond_id, limit=limit)


def search_memory(farm_id: str, query: str = "", pond_id: str = "", limit: int = 10) -> dict:
    """Alias with Mnemon naming for scoped durable memory search."""
    return search_farm_memory(farm_id=farm_id, query=query, pond_id=pond_id, limit=limit)


def _pond_history_bucket(content: str, memory_type: str, tags: list[str]) -> str:
    text = f"{content} {' '.join(tags or [])}".lower()
    if "harvest" in text or "panen" in text or "outcome" in text:
        return "past_harvest_outcomes"
    if memory_type == "advice" or any(word in text for word in ["worked", "improved", "recovered", "action", "aeration"]):
        return "what_worked_before"
    if any(word in text for word in ["recurring", "repeat", "low do", "nh3", "water", "issue", "risk"]):
        return "recurring_issues"
    return "notes"


def get_pond_history(farm_id: str, pond_id: str, limit: int = 30) -> dict:
    """Return grouped pond memory useful for recommendations and farmer review."""
    groups = {
        "recurring_issues": [],
        "what_worked_before": [],
        "past_harvest_outcomes": [],
        "notes": [],
    }
    memories = list(
        AgentMemory.objects(farm_id=farm_id, pond_id=pond_id).order_by("-created_at")[:limit]
    )
    observations = list(
        MemoryObservation.objects(farm_id=farm_id, pond_id=pond_id).order_by("-created_at")[:limit]
    )

    for memory in memories:
        tags = list(memory.tags or [])
        bucket = _pond_history_bucket(memory.content, memory.memory_type, tags)
        groups[bucket].append({
            "source_ref": f"agent_memory:{memory.id}",
            "type": memory.memory_type,
            "content": memory.content,
            "cycle_id": memory.cycle_id or None,
            "confidence": memory.confidence,
            "is_verified": memory.is_verified,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
        })

    for observation in observations:
        bucket = _pond_history_bucket(observation.content, observation.observation_type, [])
        groups[bucket].append({
            "source_ref": f"memory_observation:{observation.id}",
            "type": observation.observation_type,
            "content": observation.content,
            "cycle_id": observation.cycle_id or None,
            "confidence": observation.confidence,
            "is_verified": observation.is_verified,
            "created_at": observation.created_at.isoformat() if observation.created_at else None,
        })

    return {
        "farm_id": farm_id,
        "pond_id": pond_id,
        "count": sum(len(values) for values in groups.values()),
        **groups,
    }


def save_farm_memory(farm_id: str, memory_type: str, content: str,
                     pond_id: str = "", cycle_id: str = "", tags: list = None,
                     confidence: float = 0.7, confirmed: bool = False,
                     current_user_id: str = "") -> dict:
    """Persist a durable memory for this farm."""
    from .memory_retrieval import index_agent_memory, index_memory_observation
    if not confirmed:
        return {
            "saved": False,
            "error": "Memory was not saved because farmer confirmation is required.",
        }
    valid_types = {"fact", "preference", "event", "advice", "note"}
    if memory_type not in valid_types:
        memory_type = "note"
    farm = Farm.objects(id=farm_id).first()
    if not farm:
        return {"error": f"Farm {farm_id} not found"}
    if current_user_id and str(farm.user_id) != str(current_user_id):
        return {"error": "Farm not found or not accessible"}
    memory = AgentMemory.objects.create(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id or "",
        cycle_id=cycle_id or "",
        memory_type=memory_type,
        content=content,
        tags=tags or [],
        source="user_input",
        confidence=min(max(confidence, 0.0), 1.0),
        is_verified=True,
    )
    index_agent_memory(memory)
    observation = _store_memory_observation(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id,
        cycle_id=cycle_id,
        memory_type=memory_type,
        content=content,
        source_type="farmer",
        is_verified=True,
        source_ref=f"agent_memory:{memory.id}",
    )
    index_memory_observation(observation)
    return {"saved": True, "memory_type": memory_type, "content": content, "confidence": confidence}


def get_latest_water_quality(cycle_id: str) -> dict:
    """Return the single most-recent water quality reading for a cycle."""
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No water quality data", "cycle_id": cycle_id}

    rows = sorted([r for r in cd.result_data if r.get("doc")], key=lambda x: x["doc"])
    if not rows:
        return {"error": "No readings found", "cycle_id": cycle_id}

    latest = rows[-1]
    from teramina.helpers.constant_value import Constant
    do_val = latest.get("do_avg")
    nh3_val = latest.get("nh3")
    return {
        "cycle_id": cycle_id,
        "doc": latest.get("doc"),
        "do_mg_l": do_val,
        "do_status": (
            "critical" if do_val and do_val < Constant.DO_SUITABLE_MIN
            else "warning" if do_val and do_val < Constant.DO_OPTIMAL_MIN
            else "ok"
        ) if do_val is not None else "unknown",
        "temp_c": latest.get("temp_avg"),
        "nh3_mg_l": nh3_val,
        "nh3_status": (
            "critical" if nh3_val and nh3_val > Constant.NH3_SUITABLE_MAX
            else "warning" if nh3_val and nh3_val > Constant.NH3_OPTIMAL_MAX * 0.8
            else "ok"
        ) if nh3_val is not None else "unknown",
        "ph": latest.get("ph"),
        "salinity_ppt": latest.get("salinity"),
        "turbidity_ntu": latest.get("turbidity"),
        "recorded_at_doc": latest.get("doc"),
    }


# Tool definitions for Claude API
TOOL_DEFINITIONS = [
    {
        "name": "get_farm_overview",
        "description": "Get all ponds and active cycles for a farm with current metrics.",
        "input_schema": {
            "type": "object",
            "properties": {"farm_id": {"type": "string", "description": "Farm ID"}},
            "required": ["farm_id"],
        },
    },
    {
        "name": "get_cycle_metrics",
        "description": "Get current performance metrics for a cycle: ABW, DO, temp, NH3, feed given.",
        "input_schema": {
            "type": "object",
            "properties": {"cycle_id": {"type": "string", "description": "Cycle ID"}},
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_latest_water_quality",
        "description": (
            "Get the single most-recent water quality reading for a cycle: DO, temp, NH3, pH, salinity, turbidity — "
            "with status flags (ok/warning/critical). Use for 'what is the current DO?' questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"cycle_id": {"type": "string"}},
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_water_quality_trend",
        "description": "Get water quality readings (DO, temp, NH3, pH, salinity) over the last N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string"},
                "days": {"type": "integer", "default": 7},
            },
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_forecast",
        "description": "Get production forecast: optimal harvest DOC, projected biomass and profit.",
        "input_schema": {
            "type": "object",
            "properties": {"cycle_id": {"type": "string"}},
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_cost_breakdown",
        "description": "Get total cost and breakdown by category for a cycle.",
        "input_schema": {
            "type": "object",
            "properties": {"cycle_id": {"type": "string"}},
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_growth_trend",
        "description": "Get ABW progression and SGR (specific growth rate) over the last N days. Use to diagnose slow growth or compare to expected benchmarks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string"},
                "days": {"type": "integer", "default": 14, "description": "How many days to look back"},
            },
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_feeding_summary",
        "description": "Get feeding summary: total feed given, leftover rate, and feeding status. Use to assess overfeeding or appetite issues.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string"},
                "days": {"type": "integer", "default": 7, "description": "Recent days to assess leftover rate"},
            },
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_cycle_timeline",
        "description": (
            "Get a chronological timeline of key events for a cycle: water quality "
            "anomalies, alerts, and stored memories. Use for 'what happened in this cycle?' questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string"},
                "limit": {"type": "integer", "default": 20, "description": "Max events to return"},
            },
            "required": ["cycle_id"],
        },
    },
    {
        "name": "compare_scenarios",
        "description": (
            "Compare harvest profit and yield projections for multiple DOC options. "
            "Use when the farmer asks whether to harvest now vs. waiting, or wants to "
            "evaluate different timing options."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string"},
                "harvest_docs": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of harvest DOC values to compare (e.g. [70, 80, 90])",
                },
            },
            "required": ["cycle_id", "harvest_docs"],
        },
    },
    {
        "name": "log_farmer_action",
        "description": (
            "Record a confirmed farmer action and its observed outcome as a durable memory. "
            "Call after the farmer confirms they took an action (e.g. 'I increased aeration', "
            "'I reduced feed by 10%') so future sessions can reference what worked."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string"},
                "action_description": {"type": "string", "description": "What the farmer did"},
                "outcome": {"type": "string", "description": "Observed result after the action"},
                "pond_id": {"type": "string"},
                "cycle_id": {"type": "string"},
            },
            "required": ["farm_id", "action_description"],
        },
    },
    {
        "name": "create_reminder",
        "description": (
            "Create a follow-up reminder or task for the farmer. Use when the farmer asks to be reminded "
            "about something, or when a proactive follow-up is needed (e.g., 'check DO tomorrow', "
            "'confirm aeration was done', 'harvest window review in 3 days')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string"},
                "title": {"type": "string", "description": "Short reminder title"},
                "due_in_hours": {"type": "integer", "description": "Hours from now when this should be checked"},
                "description": {"type": "string", "description": "Why this reminder was created"},
                "pond_id": {"type": "string"},
                "cycle_id": {"type": "string"},
                "task_type": {
                    "type": "string",
                    "enum": ["reminder", "follow_up", "check", "action"],
                    "default": "reminder",
                },
            },
            "required": ["farm_id", "title", "due_in_hours"],
        },
    },
    {
        "name": "search_memory",
        "description": (
            "Search scoped durable Mnemon memories for this farm: facts, preferences, past events, "
            "advice history, and farmer notes. Prefer this tool for memory retrieval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string", "description": "Farm ID"},
                "query": {"type": "string", "description": "Keyword or topic to search for"},
                "pond_id": {"type": "string", "description": "Optional: filter to a specific pond"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["farm_id"],
        },
    },
    {
        "name": "search_farm_memory",
        "description": (
            "Search durable memories for this farm: facts, preferences, past events, "
            "advice history, and farmer notes. Call this at the start of a conversation "
            "to retrieve relevant context before answering."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string", "description": "Farm ID"},
                "query": {"type": "string", "description": "Keyword or topic to search for"},
                "pond_id": {"type": "string", "description": "Optional: filter to a specific pond"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["farm_id"],
        },
    },
    {
        "name": "get_pond_history",
        "description": (
            "Get grouped durable memory for one pond: recurring issues, what worked before, "
            "past harvest outcomes, and notes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string", "description": "Farm ID"},
                "pond_id": {"type": "string", "description": "Pond ID"},
                "limit": {"type": "integer", "default": 30},
            },
            "required": ["farm_id", "pond_id"],
        },
    },
    {
        "name": "save_farm_memory",
        "description": (
            "Persist an important fact, preference, event, or advice outcome as a durable memory. "
            "Use when the farmer shares something that should be remembered across sessions: "
            "pond problems, preferences, past incidents, confirmed action outcomes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string"},
                "memory_type": {
                    "type": "string",
                    "enum": ["fact", "preference", "event", "advice", "note"],
                },
                "content": {"type": "string", "description": "What to remember"},
                "pond_id": {"type": "string", "description": "Optional: relevant pond"},
                "cycle_id": {"type": "string", "description": "Optional: relevant cycle"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords for retrieval (e.g. ['do', 'water_quality', 'aerator'])",
                },
                "confidence": {
                    "type": "number",
                    "description": (
                        "How confident you are in this memory (0.0–1.0). Use 0.9+ for farmer-confirmed "
                        "facts and lower values only when the farmer explicitly confirms uncertainty."
                    ),
                },
                "confirmed": {
                    "type": "boolean",
                    "description": (
                        "Must be true only after the farmer explicitly confirms this should be remembered. "
                        "If false or omitted, the memory will not be saved."
                    ),
                },
            },
            "required": ["farm_id", "memory_type", "content", "confirmed"],
        },
    },
]

TOOL_REGISTRY = {
    "get_latest_water_quality": get_latest_water_quality,
    "get_farm_overview": get_farm_overview,
    "get_cycle_metrics": get_cycle_metrics,
    "get_water_quality_trend": get_water_quality_trend,
    "get_forecast": get_forecast,
    "get_cost_breakdown": get_cost_breakdown,
    "get_growth_trend": get_growth_trend,
    "get_feeding_summary": get_feeding_summary,
    "get_cycle_timeline": get_cycle_timeline,
    "compare_scenarios": compare_scenarios,
    "log_farmer_action": log_farmer_action,
    "create_reminder": create_reminder,
    "search_memory": search_memory,
    "search_farm_memory": search_farm_memory,
    "get_pond_history": get_pond_history,
    "save_farm_memory": save_farm_memory,
}

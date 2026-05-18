# pylint: disable=broad-except

"""
Tool implementations for the farm assistant agent.
Each function corresponds to one Claude tool call.
"""

import logging
import math
from datetime import datetime
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
    entity = MemoryEntity.objects(
        user_id=user_id,
        farm_id=farm_id or "",
        entity_type=entity_type,
        canonical_name=canonical_name,
    ).first()
    if entity:
        if metadata:
            entity.metadata = {**(entity.metadata or {}), **metadata}
            entity.updated_at = datetime.utcnow()
            entity.save()
        return entity
    return MemoryEntity(
        user_id=user_id,
        farm_id=farm_id or "",
        entity_type=entity_type,
        canonical_name=canonical_name,
        metadata=metadata or {},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()


def _link_memory_entities(user_id: str, farm_id: str, source_id: str,
                          relation_type: str, target_id: str,
                          source_type: str = "ai_inference") -> None:
    """Create a graph relation if it does not already exist."""
    existing = MemoryRelation.objects(
        user_id=user_id,
        farm_id=farm_id or "",
        source_entity_id=source_id,
        relation_type=relation_type,
        target_entity_id=target_id,
    ).first()
    if existing:
        return
    MemoryRelation(
        user_id=user_id,
        farm_id=farm_id or "",
        source_entity_id=source_id,
        relation_type=relation_type,
        target_entity_id=target_id,
        source_type=source_type,
        created_at=datetime.utcnow(),
    ).save()


def _store_memory_observation(user_id: str, farm_id: str, memory_type: str, content: str,
                              pond_id: str = "", cycle_id: str = "", source_type: str = "ai_inference",
                              is_verified: bool = False, source_ref: str = "") -> MemoryObservation:
    """Store graph observation and connect it to farm/pond/cycle entities."""
    farm_entity = _get_or_create_memory_entity(user_id, farm_id, "farm", farm_id or "farm")
    target_entity = farm_entity
    if pond_id:
        pond_entity = _get_or_create_memory_entity(user_id, farm_id, "pond", pond_id)
        _link_memory_entities(user_id, farm_id, farm_entity.id and str(farm_entity.id), "contains", str(pond_entity.id), source_type)
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

    return MemoryObservation(
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
        created_at=datetime.utcnow(),
    ).save()


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
        pond_info = {
            "pond_id": str(pond.id),
            "pond_name": pond.name,
            "size_m2": pond.size,
            "is_active": pond.is_active,
            "active_cycle_id": pond.active_cycle_id,
        }
        if pond.active_cycle_id:
            cycle = Cycle.objects(id=pond.active_cycle_id).first()
            if cycle:
                pond_info["cycle_name"] = cycle.name
                # Get latest DOC
                cd = CycleData.objects(cycle_id=pond.active_cycle_id).first()
                if cd and cd.result_data:
                    docs = [r.get("doc") for r in cd.result_data if r.get("doc")]
                    pond_info["current_doc"] = max(docs) if docs else 0
        result["ponds"].append(pond_info)
    return result


def get_cycle_metrics(cycle_id: str) -> dict:
    """Return current performance metrics for a cycle."""
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No data found for cycle"}

    data = cd.result_data
    docs = [r.get("doc") for r in data if r.get("doc")]
    current_doc = max(docs) if docs else 0

    abw_rows = sorted([(r["doc"], r["abw"]) for r in data if r.get("abw")], key=lambda x: x[0])
    latest_abw = abw_rows[-1][1] if abw_rows else None

    recent = sorted([r for r in data if r.get("doc")], key=lambda x: x["doc"])[-7:]
    do_vals = [r.get("do_avg") for r in recent if r.get("do_avg")]
    temp_vals = [r.get("temp_avg") for r in recent if r.get("temp_avg")]
    nh3_vals = [r.get("nh3") for r in recent if r.get("nh3")]

    total_feed = sum(r.get("feed_given_kg", 0) or 0 for r in data)

    return {
        "cycle_id": cycle_id,
        "current_doc": current_doc,
        "latest_abw_g": latest_abw,
        "do_avg_7d": round(sum(do_vals) / len(do_vals), 2) if do_vals else None,
        "temp_avg_7d": round(sum(temp_vals) / len(temp_vals), 2) if temp_vals else None,
        "nh3_avg_7d": round(sum(nh3_vals) / len(nh3_vals), 3) if nh3_vals else None,
        "total_feed_given_kg": round(total_feed, 2),
        "do_status": (
            "optimal" if do_vals and sum(do_vals) / len(do_vals) >= Constant.DO_OPTIMAL_MIN
            else "below_optimal" if do_vals else "unknown"
        ),
        "nh3_status": (
            "optimal" if nh3_vals and sum(nh3_vals) / len(nh3_vals) <= Constant.NH3_OPTIMAL_MAX
            else "elevated" if nh3_vals else "unknown"
        ),
    }


def get_water_quality_trend(cycle_id: str, days: int = 7) -> dict:
    """Return water quality readings for the last N days."""
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No data found"}

    recent = sorted(
        [r for r in cd.result_data if r.get("doc")],
        key=lambda x: x["doc"]
    )[-days:]

    return {
        "cycle_id": cycle_id,
        "days_requested": days,
        "readings": [
            {
                "doc": r.get("doc"),
                "do_avg": r.get("do_avg"),
                "temp_avg": r.get("temp_avg"),
                "nh3": r.get("nh3"),
                "ph_morning": r.get("ph_morning"),
                "salinity": r.get("salinity"),
            }
            for r in recent
        ],
        "do_optimal_min": Constant.DO_OPTIMAL_MIN,
        "nh3_optimal_max": Constant.NH3_OPTIMAL_MAX,
    }


def get_forecast(cycle_id: str) -> dict:
    """Return production forecast summary."""
    fd = ForecastData.objects(cycle_id=cycle_id).first()
    if not fd or not fd.result_data:
        return {"error": "No forecast data available"}

    forecast = fd.result_data
    # Find peak profit point
    best = None
    best_profit = float("-inf")
    for row in forecast:
        profit = row.get("profit") or row.get("forecasted_profit") or 0
        if profit > best_profit:
            best_profit = profit
            best = row

    last = forecast[-1] if forecast else {}
    return {
        "cycle_id": cycle_id,
        "forecast_points": len(forecast),
        "optimal_harvest_doc": best.get("doc") if best else None,
        "optimal_harvest_profit_idr": best_profit if best_profit > float("-inf") else None,
        "forecast_final_abw_g": last.get("abw") or last.get("adj_abw"),
        "forecast_final_biomass_kg": last.get("biomass") or last.get("pond_biomass"),
        "forecast_final_doc": last.get("doc"),
    }


def get_cost_breakdown(cycle_id: str) -> dict:
    """Return cost breakdown for a cycle."""
    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return {"cycle_id": cycle_id, "total_cost_idr": 0, "breakdown": {}}
    pond = Pond.objects(id=cycle.pond_id).first()
    if not pond:
        return {"cycle_id": cycle_id, "total_cost_idr": 0, "breakdown": {}}

    cost_doc = CostData.objects(farm_id=str(pond.farm_id)).first()
    if not cost_doc or not cost_doc.data:
        return {"cycle_id": cycle_id, "total_cost_idr": 0, "breakdown": {}}

    total = sum(r.get("total", 0) or 0 for r in cost_doc.data)
    by_cat: dict = {}
    for r in cost_doc.data:
        cat = r.get("category", "other")
        by_cat[cat] = by_cat.get(cat, 0) + (r.get("total", 0) or 0)

    return {
        "cycle_id": cycle_id,
        "total_cost_idr": round(total, 0),
        "breakdown": {k: round(v, 0) for k, v in by_cat.items()},
    }


def get_growth_trend(cycle_id: str, days: int = 14) -> dict:
    """Return ABW progression and SGR trend over the last N days."""
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No data found"}

    abw_rows = sorted(
        [(r["doc"], r["abw"]) for r in cd.result_data if r.get("abw") and r.get("doc")],
        key=lambda x: x[0],
    )
    if not abw_rows:
        return {"error": "No ABW data available", "cycle_id": cycle_id}

    current_doc = abw_rows[-1][0]
    cutoff_doc = current_doc - days
    recent = [(d, w) for d, w in abw_rows if d >= cutoff_doc]

    sgr_values = []
    for i in range(1, len(recent)):
        d1, w1 = recent[i - 1]
        d2, w2 = recent[i]
        if w1 > 0 and w2 > 0 and d2 > d1:
            sgr = (math.log(w2) - math.log(w1)) / (d2 - d1) * 100
            sgr_values.append(round(sgr, 3))

    current_sgr = sgr_values[-1] if sgr_values else None
    avg_sgr = round(sum(sgr_values) / len(sgr_values), 3) if sgr_values else None
    expected_sgr = 3.5  # healthy L. vannamei benchmark

    return {
        "cycle_id": cycle_id,
        "current_doc": current_doc,
        "latest_abw_g": abw_rows[-1][1],
        "abw_trend": [{"doc": d, "abw_g": w} for d, w in recent],
        "current_sgr_pct": current_sgr,
        "avg_sgr_pct": avg_sgr,
        "expected_sgr_pct": expected_sgr,
        "growth_status": (
            "optimal" if current_sgr is not None and current_sgr >= expected_sgr
            else "below_expected" if current_sgr is not None else "unknown"
        ),
    }


def get_feeding_summary(cycle_id: str, days: int = 7) -> dict:
    """Return feeding summary: total feed given, leftover rate, and feeding status."""
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No cycle data found"}

    docs = sorted([r.get("doc") for r in cd.result_data if r.get("doc")])
    current_doc = max(docs) if docs else 0
    cutoff_doc = current_doc - days

    all_feed = list(FeedRealization.objects(cycle_id=cycle_id))
    if not all_feed:
        total_feed_kg = sum(r.get("feed_given_kg", 0) or 0 for r in cd.result_data)
        return {
            "cycle_id": cycle_id,
            "current_doc": current_doc,
            "total_feed_given_kg": round(total_feed_kg, 2),
            "note": "Detailed feed realization records not available",
        }

    total_given = sum(r.feed_given or 0 for r in all_feed)
    total_leftover = sum(r.feed_leftover or 0 for r in all_feed)
    recent = [r for r in all_feed if (r.doc or 0) >= cutoff_doc]
    recent_given = sum(r.feed_given or 0 for r in recent)
    recent_leftover = sum(r.feed_leftover or 0 for r in recent)
    leftover_rate = round(recent_leftover / recent_given * 100, 1) if recent_given > 0 else 0

    return {
        "cycle_id": cycle_id,
        "current_doc": current_doc,
        "total_feed_given_kg": round(total_given, 2),
        "total_feed_leftover_kg": round(total_leftover, 2),
        f"recent_{days}d_given_kg": round(recent_given, 2),
        f"recent_{days}d_leftover_rate_pct": leftover_rate,
        "feeding_status": (
            "overfeeding" if leftover_rate > 20
            else "slightly_high" if leftover_rate > 10 else "normal"
        ),
    }


def get_cycle_timeline(cycle_id: str, limit: int = 20) -> dict:
    """Return a chronological timeline of key events in this cycle."""
    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return {"error": f"Cycle {cycle_id} not found"}

    events = []

    cd = CycleData.objects(cycle_id=cycle_id).first()
    if cd and cd.result_data:
        for row in sorted([r for r in cd.result_data if r.get("doc")], key=lambda x: x["doc"]):
            doc = row["doc"]
            notes = []
            if row.get("do_avg") and row["do_avg"] < Constant.DO_OPTIMAL_MIN:
                notes.append(f"DO low: {row['do_avg']:.1f} mg/L")
            if row.get("nh3") and row["nh3"] > Constant.NH3_OPTIMAL_MAX:
                notes.append(f"NH3 elevated: {row['nh3']:.3f} mg/L")
            if row.get("abw") and (doc % 7 == 0 or doc == 1):
                notes.append(f"ABW: {row['abw']:.1f}g")
            if notes:
                events.append({
                    "type": "observation",
                    "doc": doc,
                    "date": None,
                    "description": "; ".join(notes),
                })

    for alert in FarmAlert.objects(cycle_id=cycle_id).order_by("created_at").limit(50):
        events.append({
            "type": "alert",
            "doc": None,
            "date": alert.created_at.isoformat() if alert.created_at else None,
            "severity": alert.severity,
            "description": alert.message,
        })

    for mem in AgentMemory.objects(cycle_id=cycle_id).order_by("created_at").limit(20):
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
    from datetime import timedelta
    farm = Farm.objects(id=farm_id).first()
    if not farm:
        return {"error": f"Farm {farm_id} not found"}
    valid_types = {"reminder", "follow_up", "check", "action"}
    if task_type not in valid_types:
        task_type = "reminder"
    due_at = datetime.utcnow() + timedelta(hours=due_in_hours)
    task = WorkflowTask(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id or "",
        cycle_id=cycle_id or "",
        task_type=task_type,
        title=title,
        description=description,
        due_at=due_at,
        created_at=datetime.utcnow(),
    ).save()
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
    farm = Farm.objects(id=farm_id).first()
    if not farm:
        return {"error": f"Farm {farm_id} not found"}
    content = f"Action: {action_description}"
    if outcome:
        content += f" | Outcome: {outcome}"
    memory = AgentMemory(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id or "",
        cycle_id=cycle_id or "",
        memory_type="advice",
        content=content,
        tags=["action", "confirmed"],
        source="user_input",
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    _store_memory_observation(
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
    return {"logged": True, "content": content}


def search_farm_memory(farm_id: str, query: str = "", pond_id: str = "", limit: int = 10) -> dict:
    """Search durable farmer memories for relevant context."""
    filters = {"farm_id": farm_id}
    if pond_id:
        filters["pond_id"] = pond_id

    memories = AgentMemory.objects(**filters).order_by("-created_at").limit(limit * 3)
    results = [
        {
            "type": m.memory_type,
            "content": m.content,
            "tags": m.tags,
            "pond_id": m.pond_id or None,
            "cycle_id": m.cycle_id or None,
            "source": m.source,
            "confidence": getattr(m, "confidence", 0.7),
            "is_verified": m.is_verified,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in memories
    ]
    observations = MemoryObservation.objects(**filters).order_by("-created_at").limit(limit * 3)
    results.extend([
        {
            "type": o.observation_type,
            "content": o.content,
            "tags": [],
            "pond_id": o.pond_id or None,
            "cycle_id": o.cycle_id or None,
            "source": o.source_type,
            "confidence": getattr(o, "confidence", 0.7),
            "is_verified": o.is_verified,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in observations
    ])
    if query:
        q = query.lower()
        results = [
            r for r in results
            if q in r["content"].lower() or any(q in t.lower() for t in (r.get("tags") or []))
        ]
    results.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return {"farm_id": farm_id, "count": len(results[:limit]), "memories": results[:limit]}


def save_farm_memory(farm_id: str, memory_type: str, content: str,
                     pond_id: str = "", cycle_id: str = "", tags: list = None,
                     confidence: float = 0.7) -> dict:
    """Persist a durable memory for this farm."""
    valid_types = {"fact", "preference", "event", "advice", "note"}
    if memory_type not in valid_types:
        memory_type = "note"
    farm = Farm.objects(id=farm_id).first()
    if not farm:
        return {"error": f"Farm {farm_id} not found"}
    memory = AgentMemory(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id or "",
        cycle_id=cycle_id or "",
        memory_type=memory_type,
        content=content,
        tags=tags or [],
        source="agent_inference",
        confidence=min(max(confidence, 0.0), 1.0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).save()
    _store_memory_observation(
        user_id=str(farm.user_id),
        farm_id=farm_id,
        pond_id=pond_id,
        cycle_id=cycle_id,
        memory_type=memory_type,
        content=content,
        source_ref=f"agent_memory:{memory.id}",
    )
    return {"saved": True, "memory_type": memory_type, "content": content, "confidence": confidence}


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
                        "facts, 0.7 for AI inferences, 0.5 for uncertain observations."
                    ),
                },
            },
            "required": ["farm_id", "memory_type", "content"],
        },
    },
]

TOOL_REGISTRY = {
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
    "search_farm_memory": search_farm_memory,
    "save_farm_memory": save_farm_memory,
}

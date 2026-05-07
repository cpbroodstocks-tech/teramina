# pylint: disable=broad-except

"""
Tool implementations for the farm assistant agent.
Each function corresponds to one Claude tool call.
"""

import logging
from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData
from teramina.cost_data.models.cost_data_model import CostData
from teramina.helpers.constant_value import Constant

logger = logging.getLogger("teramina")


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
    cost_doc = CostData.objects(farm_id=cycle_id).first()
    if not cost_doc or not cost_doc.data:
        return {"total_cost_idr": 0, "breakdown": {}}

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
]

TOOL_REGISTRY = {
    "get_farm_overview": get_farm_overview,
    "get_cycle_metrics": get_cycle_metrics,
    "get_water_quality_trend": get_water_quality_trend,
    "get_forecast": get_forecast,
    "get_cost_breakdown": get_cost_breakdown,
}

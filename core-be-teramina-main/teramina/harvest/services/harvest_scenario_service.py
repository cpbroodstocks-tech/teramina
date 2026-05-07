# pylint: disable=broad-except, too-many-locals

import logging

from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData
from teramina.cost_data.models.cost_data_model import CostData
from teramina.harvest.models.harvest_scenario_model import HarvestScenario
from teramina.helpers.constant_value import Constant
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema

logger = logging.getLogger("teramina")

# Default shrimp price per size grade (IDR/kg) — fallback if DB price unavailable
DEFAULT_PRICE_BY_SIZE = {
    "< 30": 120000,
    "31-40": 100000,
    "41-50": 90000,
    "51-60": 80000,
    "61-70": 72000,
    "71-80": 65000,
    "> 80": 58000,
}


def _abw_to_size_grade(abw_g: float) -> str:
    """Convert ABW in grams to count-per-kg size grade."""
    if abw_g <= 0:
        return "unknown"
    count_per_kg = 1000 / abw_g
    if count_per_kg < 30:
        return "< 30"
    elif count_per_kg <= 40:
        return "31-40"
    elif count_per_kg <= 50:
        return "41-50"
    elif count_per_kg <= 60:
        return "51-60"
    elif count_per_kg <= 70:
        return "61-70"
    elif count_per_kg <= 80:
        return "71-80"
    else:
        return "> 80"


def _get_price_for_abw(abw_g: float, override_price: int | None) -> float:
    """Get IDR price per kg for a given ABW."""
    if override_price:
        return float(override_price)
    grade = _abw_to_size_grade(abw_g)
    return float(DEFAULT_PRICE_BY_SIZE.get(grade, 70000))


def _build_forecast_lookup(cycle_id: str) -> dict:
    """
    Build a {doc: {abw, biomass, sr}} lookup from ForecastData.
    Returns empty dict if no forecast available.
    """
    forecast_doc = ForecastData.objects(cycle_id=cycle_id).first()
    if not forecast_doc or not forecast_doc.result_data:
        return {}
    lookup = {}
    for row in forecast_doc.result_data:
        doc = row.get("doc")
        if doc is not None:
            lookup[int(doc)] = {
                "abw": row.get("abw") or row.get("ABW"),
                "biomass": row.get("biomass") or row.get("pond_biomass"),
                "sr": row.get("sr") or row.get("survival_rate"),
            }
    return lookup


def _get_current_doc_and_cost(cycle_id: str) -> tuple:
    """
    Returns (current_doc, total_cost_to_date, daily_cost_rate).
    current_doc derived from the last entry in CycleData.
    total_cost from CostData sum.
    """
    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    current_doc = 1
    if cycle_data and cycle_data.result_data:
        docs = [r.get("doc") for r in cycle_data.result_data if r.get("doc")]
        if docs:
            current_doc = max(docs)

    cost_data = CostData.objects(farm_id=cycle_id).first()
    total_cost = 0.0
    daily_cost_rate = 0.0
    if cost_data and cost_data.data:
        total_cost = sum(r.get("total", 0) or 0 for r in cost_data.data)
        if current_doc > 0:
            daily_cost_rate = total_cost / current_doc

    return current_doc, total_cost, daily_cost_rate


def _compute_scenario_point(
    doc: int,
    current_doc: int,
    total_cost_to_date: float,
    daily_cost_rate: float,
    forecast_lookup: dict,
    override_price: int | None,
    sr_decay_pct_per_week: float = 0.0,
    partial_pct: float | None = None,
) -> dict:
    """Compute P&L for a single harvest point."""
    data = forecast_lookup.get(doc, {})
    abw_g = data.get("abw") or 0.0
    biomass_kg = data.get("biomass") or 0.0
    sr_pct = data.get("sr") or 0.0

    # Apply SR decay risk if requested
    if sr_decay_pct_per_week > 0 and doc > current_doc:
        weeks_remaining = (doc - current_doc) / 7
        decay_factor = (1 - sr_decay_pct_per_week / 100) ** weeks_remaining
        sr_pct = sr_pct * decay_factor
        biomass_kg = biomass_kg * decay_factor

    # Apply partial harvest fraction
    harvest_biomass = biomass_kg
    harvest_type = "full"
    if partial_pct is not None:
        harvest_biomass = biomass_kg * (partial_pct / 100)
        harvest_type = "partial"

    price_per_kg = _get_price_for_abw(abw_g, override_price)
    gross_revenue = harvest_biomass * price_per_kg

    # Project cost to harvest date
    days_remaining = max(0, doc - current_doc)
    projected_total_cost = total_cost_to_date + (daily_cost_rate * days_remaining)

    # For partial harvest: only allocate fraction of cost
    allocated_cost = projected_total_cost
    if partial_pct is not None:
        allocated_cost = projected_total_cost * (partial_pct / 100)

    gross_profit = gross_revenue - allocated_cost
    profit_margin = (gross_profit / gross_revenue * 100) if gross_revenue > 0 else 0
    cost_per_kg = (allocated_cost / harvest_biomass) if harvest_biomass > 0 else 0

    return {
        "doc": doc,
        "harvest_type": harvest_type,
        "partial_pct": partial_pct,
        "projected_abw_g": round(abw_g, 2),
        "projected_biomass_kg": round(biomass_kg, 2),
        "harvest_biomass_kg": round(harvest_biomass, 2),
        "projected_sr_pct": round(sr_pct, 2),
        "size_grade": _abw_to_size_grade(abw_g),
        "price_per_kg_idr": int(price_per_kg),
        "gross_revenue_idr": round(gross_revenue, 0),
        "total_cost_idr": round(allocated_cost, 0),
        "gross_profit_idr": round(gross_profit, 0),
        "profit_margin_pct": round(profit_margin, 1),
        "cost_per_kg_idr": round(cost_per_kg, 0),
    }


class HarvestScenarioService:

    @staticmethod
    def run_simulation(cycle_id: str, user_id: str, data) -> tuple:
        """Run one or more harvest scenarios and return results."""
        try:
            forecast_lookup = _build_forecast_lookup(cycle_id)
            if not forecast_lookup:
                return 400, DataErrorSchema(
                    code=400,
                    message="No forecast data available. Run the forecast first."
                )

            current_doc, total_cost, daily_cost_rate = _get_current_doc_and_cost(cycle_id)
            override_price = data.price_per_kg
            all_results = []

            # Always include "harvest now" as first point
            now_point = _compute_scenario_point(
                current_doc, current_doc, total_cost, daily_cost_rate,
                forecast_lookup, override_price
            )
            now_point["label"] = f"Harvest Now (DOC {current_doc})"
            all_results.append(now_point)

            for scenario in data.scenarios:
                if scenario.type == "date_range":
                    start = scenario.doc_start or current_doc
                    end = scenario.doc_end or Constant.MAX_DOC
                    step = scenario.step_days or 7
                    for doc in range(start, min(end + 1, Constant.MAX_DOC + 1), step):
                        if doc == current_doc:
                            continue
                        point = _compute_scenario_point(
                            doc, current_doc, total_cost, daily_cost_rate,
                            forecast_lookup, override_price
                        )
                        point["label"] = f"Harvest at DOC {doc}"
                        all_results.append(point)

                elif scenario.type == "partial":
                    pct = scenario.partial_pct or 50.0
                    doc_p = scenario.doc_partial or current_doc
                    doc_f = scenario.doc_final or (current_doc + 21)

                    partial_point = _compute_scenario_point(
                        doc_p, current_doc, total_cost, daily_cost_rate,
                        forecast_lookup, override_price, partial_pct=pct
                    )
                    partial_point["label"] = f"Partial {pct:.0f}% at DOC {doc_p}"
                    all_results.append(partial_point)

                    final_point = _compute_scenario_point(
                        doc_f, current_doc, total_cost, daily_cost_rate,
                        forecast_lookup, override_price, partial_pct=100 - pct
                    )
                    final_point["label"] = f"Final {100 - pct:.0f}% at DOC {doc_f}"
                    all_results.append(final_point)

                elif scenario.type == "price_sensitivity":
                    doc_target = scenario.doc_end or current_doc + 14
                    adjustments = [-20, -10, 0, 10, 20]
                    for adj in adjustments:
                        base = forecast_lookup.get(doc_target, {}).get("abw") or 0
                        base_price = _get_price_for_abw(base, override_price)
                        adj_price = int(base_price * (1 + adj / 100))
                        point = _compute_scenario_point(
                            doc_target, current_doc, total_cost, daily_cost_rate,
                            forecast_lookup, adj_price
                        )
                        point["label"] = f"Price {adj:+d}% at DOC {doc_target}"
                        point["price_adjustment_pct"] = adj
                        all_results.append(point)

            return 200, DataSuccessSchema(
                code=200,
                message="Simulation complete",
                payload={
                    "cycle_id": cycle_id,
                    "current_doc": current_doc,
                    "results": all_results,
                },
            )
        except Exception as exc:
            logger.exception("Simulation error for cycle %s: %s", cycle_id, exc)
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def get_presets(cycle_id: str, user_id: str) -> tuple:
        """Return standard preset scenarios: now, +7, +14, +21, model-optimal."""
        try:
            forecast_lookup = _build_forecast_lookup(cycle_id)
            current_doc, total_cost, daily_cost_rate = _get_current_doc_and_cost(cycle_id)

            presets = []
            for offset in [0, 7, 14, 21]:
                doc = current_doc + offset
                if doc > Constant.MAX_DOC:
                    break
                point = _compute_scenario_point(
                    doc, current_doc, total_cost, daily_cost_rate,
                    forecast_lookup, None
                )
                point["label"] = "Now" if offset == 0 else f"+{offset} days"
                presets.append(point)

            # Find model-optimal: highest profit in forecast
            if forecast_lookup:
                best_doc = max(
                    forecast_lookup.keys(),
                    key=lambda d: _compute_scenario_point(
                        d, current_doc, total_cost, daily_cost_rate,
                        forecast_lookup, None
                    )["gross_profit_idr"]
                )
                if best_doc != current_doc:
                    optimal = _compute_scenario_point(
                        best_doc, current_doc, total_cost, daily_cost_rate,
                        forecast_lookup, None
                    )
                    optimal["label"] = f"Model Optimal (DOC {best_doc})"
                    presets.append(optimal)

            return 200, DataSuccessSchema(
                code=200,
                message="OK",
                payload={"cycle_id": cycle_id, "presets": presets},
            )
        except Exception as exc:
            logger.exception("Presets error for cycle %s: %s", cycle_id, exc)
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def save_scenario(cycle_id: str, user_id: str, data) -> tuple:
        """Persist a named scenario."""
        try:
            scenario = HarvestScenario(
                cycle_id=cycle_id,
                user_id=user_id,
                name=data.name,
                params=data.params,
                results=data.results,
                saved=True,
            ).save()
            return 200, DataSuccessSchema(
                code=200,
                message="Scenario saved",
                payload={"id": str(scenario.id)},
            )
        except Exception as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def list_scenarios(cycle_id: str) -> tuple:
        """List saved scenarios for a cycle."""
        scenarios = HarvestScenario.objects(cycle_id=cycle_id, saved=True).order_by("-created_at")
        payload = [
            {
                "id": str(s.id),
                "name": s.name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "result_count": len(s.results),
            }
            for s in scenarios
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"scenarios": payload})

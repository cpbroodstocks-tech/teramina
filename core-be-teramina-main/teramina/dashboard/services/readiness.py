# pylint: disable=no-member
"""Dashboard data readiness checks."""

from teramina.cycle_data.models.cycle_data_model import CycleData, ResultData


DASHBOARD_REQUIRED_FIELDS = {
    "date",
    "doc",
    "category",
    "adj_abw",
    "sr",
    "initial_stocking",
    "harvest_biomass_kg",
    "biomass_kg",
    "total_biomass",
    "potential_revenue",
    "cum_total_cost",
    "cost_per_kg",
    "cost_harvest",
    "cost_energy",
    "cost_probiotics",
    "cost_other",
    "cost_labor",
    "cost_bonuss",
    "cost_feed",
}


def is_dashboard_ready_cycle(cycle_id):
    """Return whether a cycle has the records required by dashboard endpoints."""
    cycle_data = CycleData.objects(cycle_id=str(cycle_id)).only("result_data").first()
    result_data = ResultData.objects(cycle_id=str(cycle_id)).only("result_data").first()
    if not cycle_data or not cycle_data.result_data or not result_data or not result_data.result_data:
        return False

    last_result = result_data.result_data[-1]
    return isinstance(last_result, dict) and DASHBOARD_REQUIRED_FIELDS.issubset(last_result.keys())

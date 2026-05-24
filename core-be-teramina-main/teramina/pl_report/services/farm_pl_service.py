from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.pl_report.services.pl_report_service import ProfitLossService


class FarmProfitLossService:
    """Aggregate P&L across all active cycles in a farm."""

    def __init__(self, farm_id: str):
        self.farm_id = farm_id

    def get_report(self) -> dict:
        farm = Farm.objects(id=self.farm_id).first()
        if not farm:
            raise ValueError(f"Farm {self.farm_id} not found")

        ponds = list(Pond.objects(farm_id=self.farm_id).only("id", "name"))
        if not ponds:
            raise ValueError("No ponds found for this farm")

        reports = []
        failed = []
        for pond in ponds:
            cycles = Cycle.objects(pond_id=str(pond.id), is_active=True).only("id", "name")
            for cycle in cycles:
                try:
                    r = ProfitLossService(str(cycle.id)).get_report()
                    r["_pond_name"] = pond.name or ""
                    reports.append(r)
                except Exception as exc:
                    failed.append({
                        "pond_name": pond.name or str(pond.id),
                        "cycle_name": cycle.name or str(cycle.id),
                        "error": str(exc),
                    })

        if failed:
            details = "; ".join(f"{f['pond_name']}/{f['cycle_name']}: {f['error']}" for f in failed)
            raise ValueError(f"Failed to load {len(failed)} cycle(s): {details}")

        if not reports:
            raise ValueError("No active cycle data available for this farm")

        return self._aggregate(farm, reports)

    def _aggregate(self, farm, reports: list) -> dict:
        from datetime import datetime

        def _sum(field):
            return sum(r.get(field, 0) or 0 for r in reports)

        def _wsum(field, weight_field="total_harvest_kg"):
            return sum((r.get(field, 0) or 0) * (r["kpi"].get(weight_field, 0) or 0) for r in reports)

        total_harvest_kg = sum(r["kpi"]["total_harvest_kg"] for r in reports)

        # Summed financials
        total_revenue = _sum("total_revenue_idr")
        total_cogs = _sum("total_cogs_idr")
        total_opex = _sum("total_opex_idr")
        total_cost = _sum("total_cost_idr")
        gross_profit = total_revenue - total_cogs
        net_profit = total_revenue - total_cost
        gross_margin_pct = round(gross_profit / total_revenue * 100, 1) if total_revenue else 0.0
        net_margin_pct = round(net_profit / total_revenue * 100, 1) if total_revenue else 0.0

        # Weighted-average KPIs
        w = total_harvest_kg or 1
        agg_kpi = {
            "doc": max(r["kpi"]["doc"] for r in reports),
            "total_harvest_kg": round(total_harvest_kg, 1),
            "final_abw_g": round(_wsum("final_abw_g") / w, 1),
            "survival_rate_pct": round(_wsum("survival_rate_pct") / w, 1),
            "fcr": round(_wsum("fcr") / w, 2),
            "cost_per_kg_idr": round(total_cost / total_harvest_kg) if total_harvest_kg else 0,
            "revenue_per_kg_idr": round(total_revenue / total_harvest_kg) if total_harvest_kg else 0,
            "break_even_price_idr": round(total_cost / total_harvest_kg) if total_harvest_kg else 0,
        }

        # Per-pond breakdown
        per_pond = []
        for r in reports:
            per_pond.append({
                "pond_name": r["_pond_name"],
                "cycle_name": r["cycle_name"],
                "doc_range": r["doc_range"],
                "is_active": r["is_active"],
                "total_revenue_idr": r["total_revenue_idr"],
                "total_cost_idr": r["total_cost_idr"],
                "net_profit_idr": r["net_profit_idr"],
                "net_margin_pct": r["net_margin_pct"],
                "kpi": r["kpi"],
            })

        # Harvest events from all cycles (with pond label)
        all_events = []
        for r in reports:
            pond_name = r["_pond_name"]
            for evt in r["harvest_events"]:
                all_events.append({**evt, "pond_name": pond_name, "cycle_name": r["cycle_name"]})

        return {
            "farm_id": self.farm_id,
            "farm_name": farm.name or "",
            "farm_location": farm.location or "",
            "generated_at": datetime.now().isoformat(),
            "cycle_count": len(reports),
            "currency": "IDR",
            "harvest_events": all_events,
            "realized_revenue_idr": _sum("realized_revenue_idr"),
            "projected_remaining_idr": _sum("projected_remaining_idr"),
            "total_revenue_idr": round(total_revenue),
            "cost_seed_idr": _sum("cost_seed_idr"),
            "cost_feed_idr": _sum("cost_feed_idr"),
            "cost_harvest_idr": _sum("cost_harvest_idr"),
            "total_cogs_idr": round(total_cogs),
            "gross_profit_idr": round(gross_profit),
            "gross_margin_pct": gross_margin_pct,
            "cost_labor_idr": _sum("cost_labor_idr"),
            "cost_energy_idr": _sum("cost_energy_idr"),
            "cost_probiotics_idr": _sum("cost_probiotics_idr"),
            "cost_bonus_idr": _sum("cost_bonus_idr"),
            "cost_other_idr": _sum("cost_other_idr"),
            "total_opex_idr": round(total_opex),
            "total_cost_idr": round(total_cost),
            "net_profit_idr": round(net_profit),
            "net_margin_pct": net_margin_pct,
            "kpi": agg_kpi,
            "per_pond": per_pond,
        }

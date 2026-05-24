# pylint: disable=broad-except
from datetime import date, datetime, timedelta

from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import ResultData
from teramina.pl_report.services.pl_report_service import ProfitLossService


def _parse_date(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return datetime.fromisoformat(str(val)[:10]).date()
    except Exception:
        return None


def _cycle_date_range(cycle, result_data: list) -> tuple[date | None, date | None]:
    start = _parse_date(cycle.start_date) if cycle.start_date else None
    end = None
    if result_data:
        last = result_data[-1]
        end = _parse_date(last.get("date"))
        if end is None and start and last.get("doc"):
            end = start + timedelta(days=int(last["doc"]) - 1)
    if end is None:
        end = date.today()
    return start, end


class YearProfitLossService:
    """Aggregate P&L for a farm across a calendar year, pro-rating cycles that span boundaries."""

    def __init__(self, farm_id: str, year: int):
        self.farm_id = farm_id
        self.year = year

    def get_report(self) -> dict:
        farm = Farm.objects(id=self.farm_id).first()
        if not farm:
            raise ValueError(f"Farm {self.farm_id} not found")

        year_start = date(self.year, 1, 1)
        year_end = date(self.year, 12, 31)

        ponds = list(Pond.objects(farm_id=self.farm_id).only("id", "name"))
        if not ponds:
            raise ValueError("No ponds found for this farm")

        entries = []
        failed = []
        for pond in ponds:
            cycles = Cycle.objects(pond_id=str(pond.id)).only("id", "start_date", "name", "is_active")
            for cycle in cycles:
                result_obj = ResultData.objects(cycle_id=str(cycle.id)).only("result_data").first()
                if not result_obj or not result_obj.result_data:
                    continue

                c_start, c_end = _cycle_date_range(cycle, result_obj.result_data)
                if c_start is None:
                    continue

                # Skip if no overlap with target year
                if c_end < year_start or c_start > year_end:
                    continue

                overlap_start = max(c_start, year_start)
                overlap_end = min(c_end, year_end)
                overlap_days = (overlap_end - overlap_start).days + 1
                total_days = max((c_end - c_start).days + 1, 1)
                proration = overlap_days / total_days

                try:
                    report = ProfitLossService(str(cycle.id)).get_report()
                except Exception as exc:
                    failed.append({
                        "pond_name": pond.name or str(pond.id),
                        "cycle_name": cycle.name or str(cycle.id),
                        "error": str(exc),
                    })
                    continue

                entries.append({
                    "report": report,
                    "proration": proration,
                    "pond_name": pond.name or "",
                    "cycle_start": c_start.isoformat(),
                    "cycle_end": c_end.isoformat(),
                    "overlap_days": overlap_days,
                    "total_days": total_days,
                })

        if failed:
            details = "; ".join(f"{f['pond_name']}/{f['cycle_name']}: {f['error']}" for f in failed)
            raise ValueError(f"Failed to load {len(failed)} cycle(s): {details}")

        if not entries:
            raise ValueError(f"No cycle data overlapping year {self.year} for this farm")

        return self._aggregate(farm, entries)

    def _aggregate(self, farm, entries: list) -> dict:
        def _psum(field):
            return sum((e["report"].get(field, 0) or 0) * e["proration"] for e in entries)

        total_revenue = _psum("total_revenue_idr")
        total_cogs = _psum("total_cogs_idr")
        total_opex = _psum("total_opex_idr")
        total_cost = _psum("total_cost_idr")
        gross_profit = total_revenue - total_cogs
        net_profit = total_revenue - total_cost
        gross_margin_pct = round(gross_profit / total_revenue * 100, 1) if total_revenue else 0.0
        net_margin_pct = round(net_profit / total_revenue * 100, 1) if total_revenue else 0.0

        # Weighted-average KPIs (by pro-rated harvest volume — approximation)
        total_harvest_kg = sum(
            (e["report"]["kpi"]["total_harvest_kg"] or 0) * e["proration"] for e in entries
        )
        w = total_harvest_kg or 1

        def _wavg(kpi_field):
            return sum(
                (e["report"]["kpi"].get(kpi_field, 0) or 0)
                * (e["report"]["kpi"]["total_harvest_kg"] or 0)
                * e["proration"]
                for e in entries
            ) / w

        per_cycle = []
        for e in entries:
            r = e["report"]
            per_cycle.append({
                "pond_name": e["pond_name"],
                "cycle_name": r["cycle_name"],
                "cycle_start": e["cycle_start"],
                "cycle_end": e["cycle_end"],
                "overlap_days": e["overlap_days"],
                "total_days": e["total_days"],
                "proration_pct": round(e["proration"] * 100, 1),
                "prorated_revenue_idr": round(r["total_revenue_idr"] * e["proration"]),
                "prorated_cost_idr": round(r["total_cost_idr"] * e["proration"]),
                "prorated_net_profit_idr": round((r["total_revenue_idr"] - r["total_cost_idr"]) * e["proration"]),
            })

        return {
            "farm_id": self.farm_id,
            "farm_name": farm.name or "",
            "year": self.year,
            "cycle_count": len(entries),
            "generated_at": datetime.now().isoformat(),
            "currency": "IDR",
            "total_revenue_idr": round(total_revenue),
            "cost_seed_idr": round(_psum("cost_seed_idr")),
            "cost_feed_idr": round(_psum("cost_feed_idr")),
            "cost_harvest_idr": round(_psum("cost_harvest_idr")),
            "total_cogs_idr": round(total_cogs),
            "gross_profit_idr": round(gross_profit),
            "gross_margin_pct": gross_margin_pct,
            "cost_labor_idr": round(_psum("cost_labor_idr")),
            "cost_energy_idr": round(_psum("cost_energy_idr")),
            "cost_probiotics_idr": round(_psum("cost_probiotics_idr")),
            "cost_bonus_idr": round(_psum("cost_bonus_idr")),
            "cost_other_idr": round(_psum("cost_other_idr")),
            "total_opex_idr": round(total_opex),
            "total_cost_idr": round(total_cost),
            "net_profit_idr": round(net_profit),
            "net_margin_pct": net_margin_pct,
            "kpi": {
                "total_harvest_kg": round(total_harvest_kg, 1),
                "fcr": round(_wavg("fcr"), 2),
                "survival_rate_pct": round(_wavg("survival_rate_pct"), 1),
                "cost_per_kg_idr": round(total_cost / total_harvest_kg) if total_harvest_kg else 0,
                "revenue_per_kg_idr": round(total_revenue / total_harvest_kg) if total_harvest_kg else 0,
                "break_even_price_idr": round(total_cost / total_harvest_kg) if total_harvest_kg else 0,
            },
            "per_cycle": per_cycle,
            "note": "Financial figures are pro-rated for cycles that span year boundaries.",
        }

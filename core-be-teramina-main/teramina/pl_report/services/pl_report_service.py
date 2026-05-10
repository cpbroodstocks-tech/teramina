# pylint: disable=broad-except
from datetime import datetime

import pandas as pd

from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import ResultData
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.benchmark.models.benchmark_model import BenchmarkCohort
from teramina.pond.models.pond_model import Pond


class ProfitLossService:
    """Generate a structured P&L report for a single cycle."""

    def __init__(self, cycle_id: str):
        self.cycle_id = cycle_id

    def get_report(self) -> dict:
        cycle = Cycle.objects(id=self.cycle_id).first()
        if not cycle:
            raise ValueError(f"Cycle {self.cycle_id} not found")

        pond = Pond.objects(id=cycle.pond_id).first()

        result_obj = ResultData.objects(cycle_id=self.cycle_id).only("result_data").first()
        if not result_obj or not result_obj.result_data:
            raise ValueError("No result data available for this cycle")

        df = pd.DataFrame(result_obj.result_data)

        if "category" in df.columns:
            hist_df = df[df["category"] == "historical"].copy()
        else:
            hist_df = df.copy()

        if hist_df.empty:
            raise ValueError("No historical data available")

        last_row = hist_df.iloc[-1]

        harvest_events, total_realized_revenue, total_realized_biomass = (
            self._build_harvest_events(df)
        )

        is_active = bool(cycle.is_active)
        projected_remaining = self._projected_remaining(hist_df, is_active)
        total_revenue = total_realized_revenue + (projected_remaining or 0.0)

        cost_totals, cost_seed, total_cost = self._compute_costs(hist_df)

        cogs = cost_totals["cost_feed"] + cost_totals["cost_harvest"] + cost_seed
        opex = (
            cost_totals["cost_labor"]
            + cost_totals["cost_energy"]
            + cost_totals["cost_probiotics"]
            + cost_totals["cost_bonuss"]
            + cost_totals["cost_other"]
        )

        gross_profit = total_revenue - cogs
        gross_margin_pct = round(gross_profit / total_revenue * 100, 1) if total_revenue else 0.0
        net_profit = total_revenue - total_cost
        net_margin_pct = round(net_profit / total_revenue * 100, 1) if total_revenue else 0.0

        kpi = self._build_kpi(
            last_row, total_realized_biomass, hist_df, total_revenue, total_cost, is_active
        )

        benchmark_rows, benchmark_available = self._build_benchmark(
            kpi, last_row, pond
        )

        return {
            "cycle_id": self.cycle_id,
            "cycle_name": cycle.name or "",
            "pond_id": cycle.pond_id,
            "pond_name": pond.name if pond else "",
            "start_date": cycle.start_date.date().isoformat() if cycle.start_date else None,
            "generated_at": datetime.now().isoformat(),
            "is_active": is_active,
            "doc_range": f"DOC 1–{kpi['doc']}",
            "currency": "IDR",
            "harvest_events": harvest_events,
            "realized_revenue_idr": round(total_realized_revenue),
            "projected_remaining_idr": round(projected_remaining) if projected_remaining is not None else None,
            "total_revenue_idr": round(total_revenue),
            "cost_seed_idr": round(cost_seed),
            "cost_feed_idr": round(cost_totals["cost_feed"]),
            "cost_harvest_idr": round(cost_totals["cost_harvest"]),
            "total_cogs_idr": round(cogs),
            "gross_profit_idr": round(gross_profit),
            "gross_margin_pct": gross_margin_pct,
            "cost_labor_idr": round(cost_totals["cost_labor"]),
            "cost_energy_idr": round(cost_totals["cost_energy"]),
            "cost_probiotics_idr": round(cost_totals["cost_probiotics"]),
            "cost_bonus_idr": round(cost_totals["cost_bonuss"]),
            "cost_other_idr": round(cost_totals["cost_other"]),
            "total_opex_idr": round(opex),
            "total_cost_idr": round(total_cost),
            "net_profit_idr": round(net_profit),
            "net_margin_pct": net_margin_pct,
            "kpi": kpi,
            "benchmark": benchmark_rows,
            "benchmark_available": benchmark_available,
        }

    def _build_harvest_events(self, df: pd.DataFrame):
        harvest_record = HarvestRecord.objects(cycle_id=self.cycle_id).first()
        events = []
        total_revenue = 0.0
        total_biomass = 0.0

        if not harvest_record or not harvest_record.harvest_data:
            return events, total_revenue, total_biomass

        for key, val in harvest_record.harvest_data.items():
            doc_val = val.get("doc", "")
            bio_val = val.get("biomass", "")
            rev_val = val.get("revenue", "")
            if doc_val == "" or bio_val == "" or rev_val == "":
                continue
            if not isinstance(doc_val, (int, float)) or not isinstance(bio_val, (int, float)):
                continue

            doc_val = int(doc_val)
            bio_val = float(bio_val)
            rev_val = float(rev_val)

            abw_g = 0.0
            mask = df["doc"] == doc_val
            if mask.any() and "adj_abw" in df.columns:
                abw_g = float(df.loc[mask, "adj_abw"].values[0] or 0)

            size_count = round(1000 / abw_g, 1) if abw_g > 0 else 0.0
            price_per_kg = round(rev_val / bio_val) if bio_val > 0 else 0

            events.append({
                "key": key,
                "harvest_type": "final" if key == "final" else "partial",
                "doc": doc_val,
                "biomass_kg": round(bio_val, 1),
                "size_count_per_kg": size_count,
                "price_per_kg_idr": price_per_kg,
                "revenue_idr": round(rev_val),
            })
            total_revenue += rev_val
            total_biomass += bio_val

        events.sort(key=lambda x: x["doc"])
        for i, evt in enumerate(events):
            evt["harvest_no"] = i + 1

        return events, total_revenue, total_biomass

    @staticmethod
    def _projected_remaining(hist_df: pd.DataFrame, is_active: bool):
        if not is_active:
            return None
        if "potential_revenue" not in hist_df.columns:
            return 0.0
        val = hist_df["potential_revenue"].iloc[-1]
        return max(0.0, float(val or 0))

    @staticmethod
    def _compute_costs(hist_df: pd.DataFrame):
        cols = ["cost_feed", "cost_probiotics", "cost_energy", "cost_labor", "cost_bonuss", "cost_harvest", "cost_other"]
        totals = {col: float(hist_df[col].fillna(0).sum()) if col in hist_df.columns else 0.0 for col in cols}
        seed = float(hist_df["cost_seed"].fillna(0).sum()) if "cost_seed" in hist_df.columns else 0.0

        if "cum_total_cost" in hist_df.columns:
            total = float(hist_df["cum_total_cost"].iloc[-1] or 0)
        else:
            total = sum(totals.values()) + seed

        return totals, seed, total

    @staticmethod
    def _build_kpi(last_row, total_realized_biomass, hist_df, total_revenue, total_cost, is_active):
        doc = int(last_row.get("doc", 0) or 0)
        fcr = float(last_row.get("fcr", 0) or 0)
        abw = float(last_row.get("adj_abw", 0) or 0)

        sr_raw = float(last_row.get("sr", 0) or 0)
        sr_pct = sr_raw * 100 if sr_raw <= 1.0 else sr_raw

        cost_per_kg = float(last_row.get("cost_per_kg", 0) or 0)
        total_biomass = float(last_row.get("total_biomass", 0) or 0)

        harvest_kg = total_realized_biomass
        if harvest_kg == 0 and not is_active and "harvest_biomass_kg" in hist_df.columns:
            harvest_kg = float(hist_df["harvest_biomass_kg"].fillna(0).sum())

        revenue_per_kg = total_revenue / total_biomass if total_biomass > 0 else 0.0
        break_even = total_cost / total_biomass if total_biomass > 0 else 0.0

        return {
            "doc": doc,
            "total_harvest_kg": round(harvest_kg, 1),
            "final_abw_g": round(abw, 1),
            "survival_rate_pct": round(sr_pct, 1),
            "fcr": round(fcr, 2),
            "cost_per_kg_idr": round(cost_per_kg),
            "revenue_per_kg_idr": round(revenue_per_kg),
            "break_even_price_idr": round(break_even),
        }

    @staticmethod
    def _build_benchmark(kpi: dict, last_row, pond):
        rows = []
        available = False
        try:
            doc = kpi["doc"]
            doc_bucket = ProfitLossService._doc_bucket(doc)
            initial_stocking = float(last_row.get("initial_stocking", 0) or 0)
            pond_size = float(pond.size) if pond and pond.size else 0.0
            density = initial_stocking / pond_size if pond_size > 0 else 0.0
            density_bucket = ProfitLossService._density_bucket(density)

            cohort = BenchmarkCohort.objects(
                doc_bucket=doc_bucket, density_bucket=density_bucket, suppressed=False
            ).first() or BenchmarkCohort.objects(doc_bucket=doc_bucket, suppressed=False).first()

            if not cohort:
                return rows, available

            available = True
            specs = [
                ("FCR", "fcr", kpi["fcr"], "", True),
                ("Survival Rate", "sr", kpi["survival_rate_pct"], "%", False),
                ("Cost / kg", "cost_per_kg", kpi["cost_per_kg_idr"], "IDR", True),
            ]
            for label, field, my_val, unit, lower_better in specs:
                data = getattr(cohort, field, None)
                if data:
                    rows.append({
                        "metric": label,
                        "your_value": my_val,
                        "peer_p25": data.get("p25"),
                        "peer_p50": data.get("p50"),
                        "peer_p75": data.get("p75"),
                        "unit": unit,
                        "lower_is_better": lower_better,
                    })
        except Exception:
            pass
        return rows, available

    @staticmethod
    def _doc_bucket(doc: int) -> str:
        if doc <= 60:
            return "1-60"
        if doc <= 90:
            return "61-90"
        if doc <= 120:
            return "91-120"
        return "121+"

    @staticmethod
    def _density_bucket(density: float) -> str:
        if density < 50:
            return "<50"
        if density <= 100:
            return "50-100"
        if density <= 200:
            return "100-200"
        return ">200"

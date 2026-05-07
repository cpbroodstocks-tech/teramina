# pylint: disable=broad-except, too-many-locals, too-many-branches

import hashlib
import logging
from datetime import datetime

import numpy as np

from teramina.farm.models.farm_model import Farm
from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.cost_data.models.cost_data_model import CostData
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema

from ..models.benchmark_model import (
    BenchmarkParticipation,
    BenchmarkCohort,
    CompletedCycleMetrics,
)

logger = logging.getLogger("teramina")

MIN_COHORT_SIZE = 5


# ── Cohort helpers ─────────────────────────────────────────────────────────────

def _doc_bucket(doc: int) -> str:
    if doc <= 60:
        return "1-60"
    elif doc <= 90:
        return "61-90"
    elif doc <= 120:
        return "91-120"
    else:
        return "121+"


def _density_bucket(density: float) -> str:
    if density < 50:
        return "<50"
    elif density < 100:
        return "50-100"
    elif density < 200:
        return "100-200"
    else:
        return ">200"


def _pond_size_bucket(size_m2: float) -> str:
    if size_m2 < 500:
        return "<500"
    elif size_m2 <= 2000:
        return "500-2000"
    else:
        return ">2000"


def _cohort_key(species: str, doc_bucket: str, density_bucket: str,
                region: str, pond_size_bucket: str) -> str:
    raw = f"{species}|{doc_bucket}|{density_bucket}|{region}|{pond_size_bucket}"
    return hashlib.md5(raw.encode()).hexdigest()


def _percentile_dict(values: list) -> dict:
    """Compute percentile statistics for a list of floats."""
    arr = np.array([v for v in values if v is not None and not np.isnan(v)])
    if len(arr) == 0:
        return {}
    return {
        "p10": round(float(np.percentile(arr, 10)), 3),
        "p25": round(float(np.percentile(arr, 25)), 3),
        "p50": round(float(np.percentile(arr, 50)), 3),
        "p75": round(float(np.percentile(arr, 75)), 3),
        "p90": round(float(np.percentile(arr, 90)), 3),
        "mean": round(float(np.mean(arr)), 3),
        "n": len(arr),
    }


def _percentile_rank(value: float, dist: dict) -> int:
    """
    Estimate what percentile `value` sits at within a distribution dict.
    Returns 0-100.
    """
    if not dist or value is None:
        return 50
    checkpoints = [(dist.get("p10", 0), 10), (dist.get("p25", 0), 25),
                   (dist.get("p50", 0), 50), (dist.get("p75", 0), 75),
                   (dist.get("p90", 0), 90)]
    for threshold, pct in reversed(checkpoints):
        if value >= threshold:
            return pct
    return 5


# ── Metric extraction ──────────────────────────────────────────────────────────

def _extract_cycle_metrics(cycle_id: str, farm_id: str, pond_id: str,
                           user_id: str, region: str) -> dict | None:
    """Compute final metrics for a completed cycle."""
    pond = Pond.objects(id=pond_id).first()
    if not pond or not pond.size:
        return None

    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return None

    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    if not cycle_data or not cycle_data.result_data:
        return None

    data = cycle_data.result_data
    docs = [r.get("doc") for r in data if r.get("doc")]
    final_doc = max(docs) if docs else 0
    if final_doc == 0:
        return None

    # ABW samples
    abw_samples = sorted(
        [(r["doc"], r["abw"]) for r in data if r.get("abw")],
        key=lambda x: x[0],
    )
    adg = None
    if len(abw_samples) >= 2:
        first_doc, first_abw = abw_samples[0]
        last_doc, last_abw = abw_samples[-1]
        if last_doc > first_doc:
            adg = (last_abw - first_abw) / (last_doc - first_doc)

    # Total feed
    total_feed_kg = sum(r.get("feed_given_kg", 0) or 0 for r in data)

    # Final biomass (last available biomass value or estimate)
    last_biomass = None
    for r in reversed(data):
        b = r.get("biomass") or r.get("pond_biomass")
        if b:
            last_biomass = float(b)
            break

    # FCR
    fcr = None
    if total_feed_kg > 0 and last_biomass and last_biomass > 0:
        fcr = total_feed_kg / last_biomass

    # SR (last available)
    last_sr = None
    for r in reversed(data):
        sr = r.get("sr") or r.get("survival_rate")
        if sr:
            last_sr = float(sr)
            break

    # Cost per kg
    cost_doc = CostData.objects(farm_id=cycle_id).first()
    cost_per_kg = None
    revenue_per_m2 = None
    if cost_doc and cost_doc.data:
        total_cost = sum(r.get("total", 0) or 0 for r in cost_doc.data)
        if last_biomass and last_biomass > 0:
            cost_per_kg = total_cost / last_biomass

    # Biomass yield (ton/ha)
    biomass_yield = None
    if last_biomass and pond.size:
        biomass_yield = (last_biomass / 1000) / (pond.size / 10000)  # ton/ha

    stocking_density = None
    # Infer from first data point's population if available
    pop_rows = [r.get("population") for r in data if r.get("population")]
    if pop_rows and pond.size:
        stocking_density = float(pop_rows[0]) / pond.size

    return {
        "cycle_id": cycle_id,
        "farm_id": farm_id,
        "pond_id": pond_id,
        "user_id": user_id,
        "region": region,
        "stocking_density": stocking_density,
        "pond_size_m2": pond.size,
        "final_doc": final_doc,
        "fcr_final": round(fcr, 3) if fcr else None,
        "sr_final_pct": round(last_sr, 2) if last_sr else None,
        "adg_avg": round(adg, 3) if adg else None,
        "biomass_yield_ton_per_ha": round(biomass_yield, 3) if biomass_yield else None,
        "cost_per_kg_idr": round(cost_per_kg, 0) if cost_per_kg else None,
        "revenue_per_m2_idr": revenue_per_m2,
    }


# ── Service ────────────────────────────────────────────────────────────────────

class BenchmarkService:

    @staticmethod
    def opt_in(farm_id: str, user_id: str) -> tuple:
        existing = BenchmarkParticipation.objects(farm_id=farm_id).first()
        if existing:
            existing.opted_in = True
            existing.opted_in_at = datetime.utcnow()
            existing.opted_out_at = None
            existing.save()
        else:
            BenchmarkParticipation(
                farm_id=farm_id,
                user_id=user_id,
                opted_in=True,
                opted_in_at=datetime.utcnow(),
            ).save()
        return 200, DataSuccessSchema(
            code=200,
            message="Opted in to benchmarking. Your anonymized data will contribute to the next nightly aggregation.",
            payload={"farm_id": farm_id},
        )

    @staticmethod
    def opt_out(farm_id: str) -> tuple:
        participation = BenchmarkParticipation.objects(farm_id=farm_id).first()
        if participation:
            participation.opted_in = False
            participation.opted_out_at = datetime.utcnow()
            participation.save()
            # Remove this farm's cycle metrics so they're excluded from next aggregation
            CompletedCycleMetrics.objects(farm_id=farm_id).delete()
        return 200, DataSuccessSchema(
            code=200,
            message="Opted out. Your data will be removed from benchmarks in the next aggregation.",
            payload={"farm_id": farm_id},
        )

    @staticmethod
    def get_my_performance(cycle_id: str, user_id: str) -> tuple:
        """Compare this cycle's metrics against its cohort."""
        my_metrics = CompletedCycleMetrics.objects(cycle_id=cycle_id).first()
        if not my_metrics:
            return 400, DataErrorSchema(
                code=400,
                message="No benchmark data for this cycle. The cycle may still be active or has not been processed yet."
            )

        cohort_key = _cohort_key(
            "vannamei",
            _doc_bucket(my_metrics.final_doc or 90),
            _density_bucket(my_metrics.stocking_density or 100),
            my_metrics.region or "",
            _pond_size_bucket(my_metrics.pond_size_m2 or 1000),
        )
        cohort = BenchmarkCohort.objects(cohort_key=cohort_key, suppressed=False).first()
        if not cohort:
            return 400, DataErrorSchema(
                code=400,
                message="Cohort data not available yet (fewer than 5 farms in your group, or aggregation not run)."
            )

        def _build_metric(my_val, dist, lower_is_better=False):
            if my_val is None or not dist:
                return None
            rank = _percentile_rank(my_val, dist)
            if lower_is_better:
                rank = 100 - rank
            return {
                "your_value": my_val,
                "your_percentile": rank,
                **dist,
                "status": "good" if rank >= 60 else ("warning" if rank >= 30 else "below_average"),
            }

        payload = {
            "cycle_id": cycle_id,
            "cohort": {
                "doc_bucket": cohort.doc_bucket,
                "density_bucket": cohort.density_bucket,
                "region": cohort.region,
                "pond_size_bucket": cohort.pond_size_bucket,
                "sample_count": cohort.sample_count,
            },
            "metrics": {
                "fcr": _build_metric(my_metrics.fcr_final, cohort.fcr, lower_is_better=True),
                "sr": _build_metric(my_metrics.sr_final_pct, cohort.sr),
                "adg": _build_metric(my_metrics.adg_avg, cohort.adg),
                "biomass_yield": _build_metric(my_metrics.biomass_yield_ton_per_ha, cohort.biomass_yield),
                "cost_per_kg": _build_metric(my_metrics.cost_per_kg_idr, cohort.cost_per_kg, lower_is_better=True),
            },
        }
        return 200, DataSuccessSchema(code=200, message="OK", payload=payload)

    @staticmethod
    def compute_and_store_cycle_metrics(cycle_id: str) -> bool:
        """
        Extract and store metrics for a completed cycle if farm is opted in.
        Called when a cycle is marked inactive.
        """
        cycle = Cycle.objects(id=cycle_id).first()
        if not cycle:
            return False
        pond = Pond.objects(id=cycle.pond_id).first()
        if not pond:
            return False
        farm = Farm.objects(id=pond.farm_id).first()
        if not farm:
            return False

        participation = BenchmarkParticipation.objects(
            farm_id=str(farm.id), opted_in=True
        ).first()
        if not participation:
            return False

        metrics = _extract_cycle_metrics(
            cycle_id, str(farm.id), str(pond.id), str(farm.user_id), farm.location or ""
        )
        if not metrics:
            return False

        existing = CompletedCycleMetrics.objects(cycle_id=cycle_id).first()
        if existing:
            for k, v in metrics.items():
                setattr(existing, k, v)
            existing.computed_at = datetime.utcnow()
            existing.save()
        else:
            CompletedCycleMetrics(**metrics).save()
        return True

    @staticmethod
    def recompute_cohorts() -> dict:
        """
        Nightly aggregation: recompute all BenchmarkCohort documents
        from CompletedCycleMetrics of opted-in farms.
        Called by Celery Beat.
        """
        all_metrics = list(CompletedCycleMetrics.objects.all())
        if not all_metrics:
            return {"cohorts_updated": 0, "total_cycles": 0}

        # Group by cohort dimensions
        groups: dict = {}
        for m in all_metrics:
            if not m.stocking_density or not m.pond_size_m2 or not m.final_doc:
                continue
            key = _cohort_key(
                "vannamei",
                _doc_bucket(m.final_doc),
                _density_bucket(m.stocking_density),
                m.region or "",
                _pond_size_bucket(m.pond_size_m2),
            )
            if key not in groups:
                groups[key] = {
                    "metrics": [],
                    "farms": set(),
                    "doc_bucket": _doc_bucket(m.final_doc),
                    "density_bucket": _density_bucket(m.stocking_density),
                    "region": m.region or "",
                    "pond_size_bucket": _pond_size_bucket(m.pond_size_m2),
                }
            groups[key]["metrics"].append(m)
            groups[key]["farms"].add(m.farm_id)

        updated = 0
        for key, group in groups.items():
            records = group["metrics"]
            farm_count = len(group["farms"])
            suppressed = farm_count < MIN_COHORT_SIZE

            cohort_data = {
                "cohort_key": key,
                "species": "vannamei",
                "doc_bucket": group["doc_bucket"],
                "density_bucket": group["density_bucket"],
                "region": group["region"],
                "pond_size_bucket": group["pond_size_bucket"],
                "sample_count": farm_count,
                "cycle_count": len(records),
                "suppressed": suppressed,
                "computed_at": datetime.utcnow(),
                "fcr": _percentile_dict([r.fcr_final for r in records]),
                "sr": _percentile_dict([r.sr_final_pct for r in records]),
                "adg": _percentile_dict([r.adg_avg for r in records]),
                "biomass_yield": _percentile_dict([r.biomass_yield_ton_per_ha for r in records]),
                "cost_per_kg": _percentile_dict([r.cost_per_kg_idr for r in records]),
                "revenue_per_m2": _percentile_dict([r.revenue_per_m2_idr for r in records]),
            }

            existing = BenchmarkCohort.objects(cohort_key=key).first()
            if existing:
                for k, v in cohort_data.items():
                    setattr(existing, k, v)
                existing.save()
            else:
                BenchmarkCohort(**cohort_data).save()
            updated += 1

        logger.info("Benchmark cohorts recomputed: %d cohorts, %d total cycles", updated, len(all_metrics))
        return {"cohorts_updated": updated, "total_cycles": len(all_metrics)}

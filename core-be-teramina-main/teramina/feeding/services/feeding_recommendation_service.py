# pylint: disable=broad-except, too-many-locals, too-many-branches
"""
Feeding Recommendation Service

Decision framing
----------------
Feeding is a decision under uncertainty, not a deterministic lookup.
The system maintains two latent states that are not directly observable:

  B_t — true biomass (approximated by Kalman-filtered estimates)
  A_t — appetite (estimated from tray leftover observations)

The penalty function is asymmetric:
  • Overfeeding → convex cost (exponential): water quality degrades
    non-linearly; an oxygen crash can wipe out a crop.
  • Underfeeding → linear cost: growth loss proportional to deficit.

The environmental risk is modelled with a sigmoid:
  P(stress) = σ(α·FR + β/DO + γ·NH3 − intercept)
  This captures the interaction: the same FR at DO=3 is far riskier
  than at DO=6.

Three-layer decision:
  Layer 1  (DOC ≤ 30)   — blind_feed: biomass-unaware, early-stage schedule
  Layer 2  (DOC > 30)   — rule_v1:   appetite + asymmetric penalty + sigmoid risk
  Layer 3  (DOC ≥ 60,   — ml_v1:     ML model override when confidence > threshold
            confidence > ML_CONFIDENCE_THRESHOLD)
"""

import logging
import math
from datetime import datetime

import numpy as np

from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.feeding.models.feeding_recommendation_model import (
    FeedingRecommendation,
    FeedingOverride,
)
from teramina.feeding.services.appetite_state import compute_appetite_belief
from teramina.feeding.services.feeding_ml_service import FeedingMLService
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from teramina.helpers.constant_value import Constant

ML_LAYER_DOC_THRESHOLD = 60
ML_CONFIDENCE_THRESHOLD = 0.6

# Leftover thresholds for asymmetric adjustment
LEFTOVER_HIGH_THRESHOLD = 0.15   # > 15% leftover triggers overfeeding penalty
LEFTOVER_LOW_THRESHOLD = 0.02    # < 2%  leftover triggers underfeeding increase

logger = logging.getLogger("teramina")


# ─── Ration distribution helpers ──────────────────────────────────────────────

_FEEDING_WEIGHT_PRESETS: dict[int, list[float]] = {
    1: [1.0],
    2: [0.40, 0.60],
    3: [0.30, 0.20, 0.50],
    4: [0.30, 0.20, 0.10, 0.40],  # original default
}


def _feeding_time_weights(n: int) -> list[float]:
    """
    Per-ration weight distribution for n feeding slots.

    Biologically the last (evening) slot matters most for vannamei —
    shrimp are more active at dusk/night. For n > 4 the last slot
    is fixed at 0.35 and the remainder is split equally.
    """
    if n in _FEEDING_WEIGHT_PRESETS:
        return _FEEDING_WEIGHT_PRESETS[n]
    # n = 5-10: last slot fixed, rest uniform
    evening = 0.35
    each = (1.0 - evening) / (n - 1)
    weights = [each] * (n - 1) + [evening]
    total = sum(weights)
    return [round(w / total, 6) for w in weights]


# ─── Latent state helpers ──────────────────────────────────────────────────────

def _get_recent_leftover_ratio(cycle_id: str, doc: int, n_days: int = 3) -> float | None:
    """
    Average leftover ratio over last n_days.
    Only includes rations where feed_leftover was recorded (optional field).
    Returns None if no data.
    """
    records = FeedRealization.objects(
        cycle_id=cycle_id,
        doc__gte=max(1, doc - n_days),
        doc__lt=doc,
    ).only("feed_given", "feed_leftover")
    records = list(records)
    if not records:
        return None
    ratios = []
    for r in records:
        if r.feed_given and r.feed_given > 0 and r.feed_leftover is not None:
            ratios.append(r.feed_leftover / r.feed_given)
    return float(np.mean(ratios)) if ratios else None


def _get_current_metrics(cycle_id: str) -> dict:
    """Extract current ABW, DOC, biomass, DO, temp, NH3 from CycleData."""
    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    metrics = {
        "current_doc": 1,
        "abw": None,
        "do_avg": None,
        "temp_avg": None,
        "nh3": None,
        "biomass": None,
        "total_feed_given": 0.0,
    }
    if not cycle_data or not cycle_data.result_data:
        return metrics

    data = cycle_data.result_data
    docs = [r.get("doc") for r in data if r.get("doc")]
    if docs:
        metrics["current_doc"] = max(docs)

    abw_rows = [(r["doc"], r["abw"]) for r in data if r.get("abw")]
    if abw_rows:
        metrics["abw"] = sorted(abw_rows, key=lambda x: x[0])[-1][1]

    recent = sorted(
        [r for r in data if r.get("doc")],
        key=lambda x: x["doc"],
    )[-3:]
    do_vals = [r["do_avg"] for r in recent if r.get("do_avg")]
    temp_vals = [r["temp_avg"] for r in recent if r.get("temp_avg")]
    nh3_vals = [r["nh3"] for r in recent if r.get("nh3")]
    if do_vals:
        metrics["do_avg"] = float(np.mean(do_vals))
    if temp_vals:
        metrics["temp_avg"] = float(np.mean(temp_vals))
    if nh3_vals:
        metrics["nh3"] = float(np.mean(nh3_vals))

    metrics["total_feed_given"] = sum(
        r.get("feed_given_kg", 0) or 0 for r in data
    )
    return metrics


def _base_ration_from_formula(doc: int, abw: float | None, biomass: float | None) -> float:
    """
    Base ration before any probabilistic adjustments.
    Simplified biomass-% approach derived from DPI formula.
    """
    if abw and biomass:
        if abw < 5:
            feed_rate_pct = 0.10
        elif abw < 15:
            feed_rate_pct = 0.06
        else:
            feed_rate_pct = 0.03
        return round(biomass * feed_rate_pct, 2)
    elif doc <= Constant.EARLY_STAGE_DOC_THRESHOLD:
        return round(2.0 + doc * 0.05, 2)
    else:
        return round(min(2.0 + doc * 0.04, 15.0), 2)


# ─── Asymmetric penalty ────────────────────────────────────────────────────────

def _asymmetric_ration_adjustment(
    base_ration: float,
    appetite: float,
    leftover_ratio: float | None,
) -> float:
    """
    Apply asymmetric loss to the base ration.

    Overfeeding (leftover > threshold):
        penalty = 1 − exp(−k · excess_above_threshold)
        Convex: each additional % of excess is costlier than the previous.
        At 15% excess → ~0%, at 30% → ~26%, at 50% → ~63% ration reduction.

    Underfeeding (leftover < threshold):
        bonus = appetite · shortage · 3.0   (linear, appetite-modulated)
        High appetite belief → larger correction.
        Capped at MAX_UNDERFEEDING_BOOST.

    Acceptable zone (between thresholds):
        Appetite fine-tunes within ±5%: multiplier ∈ [0.95, 1.05].

    No leftover data:
        Conservative: slightly scale by appetite prior (0.85 + 0.15·appetite).
    """
    if leftover_ratio is None:
        multiplier = 0.85 + 0.15 * appetite
        return round(base_ration * multiplier, 2)

    if leftover_ratio > LEFTOVER_HIGH_THRESHOLD:
        excess = leftover_ratio - LEFTOVER_HIGH_THRESHOLD
        reduction = 1.0 - math.exp(-Constant.OVERFEEDING_CONVEXITY * excess)
        reduction = min(reduction, Constant.MAX_OVERFEEDING_REDUCTION)
        multiplier = 1.0 - reduction

    elif leftover_ratio < LEFTOVER_LOW_THRESHOLD:
        shortage = LEFTOVER_LOW_THRESHOLD - leftover_ratio
        bonus = appetite * shortage * 3.0
        multiplier = min(1.0 + bonus, Constant.MAX_UNDERFEEDING_BOOST)

    else:
        # Acceptable zone: appetite fine-tunes within ±5%
        multiplier = 0.95 + 0.10 * appetite

    return round(base_ration * multiplier, 2)


# ─── Sigmoid risk function ─────────────────────────────────────────────────────

def _sigmoid_risk_multiplier(
    ration_kg: float,
    biomass_kg: float | None,
    do_avg: float | None,
    nh3: float | None,
) -> float:
    """
    Environment-conditional risk multiplier.

    P(stress) = σ(α·FR + β/DO + γ·NH3 − intercept)

    Key insight: the same feeding rate at DO=3 vs DO=6 carries
    completely different risk. This captures that interaction.

    Returns a multiplier in (1 − MAX_RISK_REDUCTION, 1.0].
    At typical conditions (DO=6, NH3=0.1, FR=3%): ~0.94  (minor reduction)
    At stressed (DO=3, NH3=0.8, FR=8%):           ~0.83  (17% reduction)
    At severe   (DO=2, NH3=1.5, FR=10%):           ~0.73  (27% reduction)
    """
    fr = (ration_kg / biomass_kg) if biomass_kg and biomass_kg > 0 else 0.0
    do_val = do_avg if do_avg and do_avg > 0 else 0.1   # avoid div/0

    risk_score = (
        Constant.RISK_ALPHA * fr
        + Constant.RISK_BETA / do_val
        + Constant.RISK_GAMMA * (nh3 or 0.0)
        - Constant.RISK_INTERCEPT
    )
    risk = 1.0 / (1.0 + math.exp(-risk_score))         # σ(score) ∈ (0, 1)
    penalty = Constant.MAX_RISK_REDUCTION * risk
    return round(1.0 - penalty, 4)


# ─── Reason builder ───────────────────────────────────────────────────────────

def _build_adjustment_reason(
    base_ration: float,
    final_ration: float,
    leftover_ratio: float | None,
    do_avg: float | None,
    nh3: float | None,
    appetite: float,
    confidence: float,
) -> str:
    parts = []
    if leftover_ratio is not None:
        if leftover_ratio > LEFTOVER_HIGH_THRESHOLD:
            parts.append(
                f"overfeeding penalty applied (leftover {leftover_ratio:.0%}; "
                f"exponential reduction)"
            )
        elif leftover_ratio < LEFTOVER_LOW_THRESHOLD:
            parts.append(
                f"underfeeding correction (leftover {leftover_ratio:.0%}; "
                f"appetite={appetite:.2f})"
            )
    if do_avg is not None and do_avg < Constant.DO_OPTIMAL_MIN:
        parts.append(f"DO risk ({do_avg:.1f} mg/L — sigmoid penalty applied)")
    if nh3 is not None and nh3 > Constant.NH3_OPTIMAL_MAX:
        parts.append(f"NH3 elevated ({nh3:.3f} mg/L — sigmoid penalty applied)")
    if confidence < 0.3:
        parts.append(f"low appetite confidence ({confidence:.0%}) — conservative estimate")
    if not parts:
        return "standard recommendation"
    delta_pct = (final_ration - base_ration) / base_ration * 100 if base_ration else 0
    direction = "↓" if delta_pct < 0 else "↑"
    parts.insert(0, f"ration {direction}{abs(delta_pct):.1f}% from base")
    return "; ".join(parts)


# ─── Service ──────────────────────────────────────────────────────────────────

class FeedingRecommendationService:

    @staticmethod
    def get_recommendation(cycle_id: str, doc: int, n_rations: int = 4) -> tuple:
        """
        Get or generate feeding recommendation for a specific DOC.

        Parameters
        ----------
        n_rations : int
            Number of feeding slots (1-10). Controls ration split weights.
        """
        try:
            n_rations = max(1, min(n_rations, Constant.MAX_FEED_TIME))

            # Return cached if exists for this DOC
            existing = FeedingRecommendation.objects(
                cycle_id=cycle_id, doc=doc
            ).first()
            if existing:
                return 200, DataSuccessSchema(
                    code=200,
                    message="OK",
                    payload={
                        "cycle_id": cycle_id,
                        "doc": doc,
                        "recommended_ration_kg": existing.recommended_ration_kg,
                        "recommended_frequency": existing.recommended_frequency,
                        "ration_per_feeding": existing.ration_per_feeding,
                        "adjustment_reason": existing.adjustment_reason,
                        "model_layer": existing.model_layer,
                        "appetite_belief": existing.features_used.get("appetite_belief"),
                    },
                )

            metrics = _get_current_metrics(cycle_id)
            abw = metrics.get("abw")
            do_avg = metrics.get("do_avg")
            nh3 = metrics.get("nh3")
            biomass = metrics.get("biomass")

            # ── Latent state estimation ───────────────────────────────────────
            leftover_ratio = _get_recent_leftover_ratio(cycle_id, doc)
            appetite_belief = compute_appetite_belief(cycle_id, doc)
            appetite = appetite_belief["appetite"]
            appetite_confidence = appetite_belief["confidence"]

            # ── Layer selection ───────────────────────────────────────────────
            if doc <= Constant.EARLY_STAGE_DOC_THRESHOLD:
                model_layer = "blind_feed"
            else:
                model_layer = "rule_v1"

            # ── Base ration ───────────────────────────────────────────────────
            base_ration = _base_ration_from_formula(doc, abw, biomass)

            # ── Asymmetric adjustment (appetite + leftover) ───────────────────
            adjusted_ration = _asymmetric_ration_adjustment(
                base_ration, appetite, leftover_ratio
            )

            # ── Sigmoid risk cap (DO + NH3 + feed-load interaction) ───────────
            risk_mult = _sigmoid_risk_multiplier(adjusted_ration, biomass, do_avg, nh3)
            adjusted_ration = round(adjusted_ration * risk_mult, 2)

            # ── Layer 3: ML override ──────────────────────────────────────────
            final_ration = adjusted_ration
            final_confidence = appetite_confidence
            final_model_version = "2.0"
            ml_reason = None

            if doc >= ML_LAYER_DOC_THRESHOLD:
                ml_result = FeedingMLService.predict(cycle_id, doc)
                if (
                    ml_result is not None
                    and ml_result.get("confidence", 0) > ML_CONFIDENCE_THRESHOLD
                ):
                    final_ration = ml_result["recommended_kg"]
                    final_confidence = ml_result["confidence"]
                    final_model_version = ml_result.get("model_version", "ml")
                    model_layer = "ml_v1"
                    ml_reason = ml_result.get("shap_explanation", "")

            # ── Ration split ──────────────────────────────────────────────────
            weights = _feeding_time_weights(n_rations)
            ration_per_feeding = [round(final_ration * w, 3) for w in weights]

            # ── Reason string ─────────────────────────────────────────────────
            if model_layer == "ml_v1":
                reason = f"ML model ({final_model_version})"
                if ml_reason:
                    reason += f": {ml_reason}"
            else:
                reason = _build_adjustment_reason(
                    base_ration, final_ration, leftover_ratio,
                    do_avg, nh3, appetite, appetite_confidence,
                )

            features = {
                "abw_g": abw,
                "do_avg_3d": do_avg,
                "temp_avg_3d": metrics.get("temp_avg"),
                "nh3_avg_3d": nh3,
                "leftover_ratio_3d": leftover_ratio,
                "biomass_kg": biomass,
                "appetite_belief": {
                    "appetite": appetite,
                    "confidence": appetite_confidence,
                    "n_observations": appetite_belief["n_observations"],
                },
                "risk_multiplier": risk_mult,
                "base_ration_kg": base_ration,
            }

            FeedingRecommendation(
                cycle_id=cycle_id,
                doc=doc,
                recommended_ration_kg=final_ration,
                recommended_frequency=n_rations,
                ration_per_feeding=ration_per_feeding,
                adjustment_reason=reason,
                model_layer=model_layer,
                model_version=final_model_version,
                confidence=final_confidence,
                features_used=features,
            ).save()

            return 200, DataSuccessSchema(
                code=200,
                message="OK",
                payload={
                    "cycle_id": cycle_id,
                    "doc": doc,
                    "recommended_ration_kg": final_ration,
                    "recommended_frequency": n_rations,
                    "ration_per_feeding": ration_per_feeding,
                    "adjustment_reason": reason,
                    "model_layer": model_layer,
                    "appetite_belief": {
                        "appetite": appetite,
                        "confidence": appetite_confidence,
                    },
                },
            )
        except Exception as exc:
            logger.exception(
                "Recommendation error for cycle %s DOC %s: %s", cycle_id, doc, exc
            )
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def record_override(cycle_id: str, doc: int, data) -> tuple:
        """Log a farmer override — used as training signal for Layer 3."""
        try:
            rec = FeedingRecommendation.objects(cycle_id=cycle_id, doc=doc).first()
            FeedingOverride(
                cycle_id=cycle_id,
                doc=doc,
                recommended_kg=rec.recommended_ration_kg if rec else None,
                actual_kg=data.actual_kg,
                override_reason=data.override_reason or "",
            ).save()
            return 200, DataSuccessSchema(
                code=200,
                message="Override recorded",
                payload={"cycle_id": cycle_id, "doc": doc},
            )
        except Exception as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def get_history(cycle_id: str) -> tuple:
        """Return last 30 days of recommendations for a cycle."""
        recs = FeedingRecommendation.objects(
            cycle_id=cycle_id
        ).order_by("-doc").limit(30)
        payload = [
            {
                "doc": r.doc,
                "recommended_ration_kg": r.recommended_ration_kg,
                "adjustment_reason": r.adjustment_reason,
                "model_layer": r.model_layer,
                "appetite_belief": r.features_used.get("appetite_belief"),
            }
            for r in recs
        ]
        return 200, DataSuccessSchema(
            code=200, message="OK", payload={"history": payload}
        )

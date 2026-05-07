# pylint: disable=broad-except
"""
Latent appetite belief state.

Model
-----
A_t ∈ [0, 1]  where 1 = maximum appetite, 0 = fully satiated.

Observation signal
  tray leftover_ratio = leftover_kg / feed_given_kg
  low leftover → high appetite   (inverse relationship)
  Records with no leftover entry are excluded from the signal
  (optional leftover tracking means absence ≠ zero leftover).

Update rule
  Exponentially weighted average across last n_days:
    w_i  = exp(-λ · days_ago)          λ = DECAY_LAMBDA
    A_t  = Σ(w_i · (1 − lr_i)) / Σ(w_i)

  Daily lr_i is averaged across all ration slots recorded that day.

Confidence
  confidence = min(n_days_with_data / N_FULL_CONFIDENCE_DAYS, 1.0)
  Drops toward 0 when few observations exist.

Output
  {
    "appetite":       float ∈ [0, 1],
    "confidence":     float ∈ [0, 1],
    "n_observations": int            # days contributing to estimate
  }
"""

import logging
from typing import Optional

import numpy as np

from teramina.feeding.models.feed_realization_model import FeedRealization

DECAY_LAMBDA = 0.4              # per-day exponential decay factor
N_FULL_CONFIDENCE_DAYS = 7      # days until confidence reaches 1.0
NEUTRAL_APPETITE = 0.5          # prior with no data
NEUTRAL_CONFIDENCE = 0.0

logger = logging.getLogger("teramina")


def compute_appetite_belief(
    cycle_id: str,
    doc: int,
    n_days: int = 7,
) -> dict:
    """
    Estimate current appetite belief from recent tray observations.

    Only rations where feed_leftover IS recorded contribute.
    Rations with feed_leftover=None are skipped (optional reading).
    """
    start_doc = max(1, doc - n_days)
    records = list(
        FeedRealization.objects(
            cycle_id=cycle_id,
            doc__gte=start_doc,
            doc__lt=doc,
        ).only("doc", "feed_given", "feed_leftover")
    )

    if not records:
        return {
            "appetite": NEUTRAL_APPETITE,
            "confidence": NEUTRAL_CONFIDENCE,
            "n_observations": 0,
        }

    # Group by doc — only include rations that have a leftover reading
    per_doc: dict[int, list[float]] = {}
    for r in records:
        if r.feed_given and r.feed_given > 0 and r.feed_leftover is not None:
            ratio = r.feed_leftover / r.feed_given
            per_doc.setdefault(r.doc, []).append(float(ratio))

    if not per_doc:
        return {
            "appetite": NEUTRAL_APPETITE,
            "confidence": NEUTRAL_CONFIDENCE,
            "n_observations": 0,
        }

    # Exponentially weighted appetite estimate
    weighted_sum = 0.0
    weight_total = 0.0
    for obs_doc, ratios in per_doc.items():
        days_ago = doc - obs_doc           # 1 = yesterday, 7 = a week ago
        avg_ratio = float(np.mean(ratios))
        appetite_obs = float(np.clip(1.0 - avg_ratio, 0.0, 1.0))
        w = float(np.exp(-DECAY_LAMBDA * days_ago))
        weighted_sum += w * appetite_obs
        weight_total += w

    appetite = weighted_sum / weight_total
    confidence = min(len(per_doc) / N_FULL_CONFIDENCE_DAYS, 1.0)

    return {
        "appetite": round(appetite, 4),
        "confidence": round(confidence, 4),
        "n_observations": len(per_doc),
    }

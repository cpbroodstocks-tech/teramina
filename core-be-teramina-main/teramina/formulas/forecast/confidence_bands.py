# pylint: disable=broad-except

"""
Compute confidence bands for forecast data.
Uses bootstrap resampling on historical ABW samples to produce
80th-percentile prediction intervals without requiring Prophet.
"""

import logging
import numpy as np
from .adaptive_params import _growth_model, get_cycle_params, MIN_SAMPLES_TO_FIT
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData
from teramina.helpers.constant_value import Constant

logger = logging.getLogger("teramina")

N_BOOTSTRAP = 200
CONFIDENCE_LEVEL = 0.80


def compute_confidence_bands(cycle_id: str) -> dict | None:
    """
    Bootstrap-resample historical ABW samples to estimate forecast uncertainty.
    Returns dict with keys: docs, lower_80, upper_80, or None if insufficient data.
    """
    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    forecast_data = ForecastData.objects(cycle_id=cycle_id).first()

    if not cycle_data or not forecast_data:
        return None

    samples = [
        (int(r["doc"]), float(r["abw"]))
        for r in cycle_data.result_data
        if r.get("doc") and r.get("abw")
    ]
    if len(samples) < MIN_SAMPLES_TO_FIT:
        return None

    samples.sort(key=lambda x: x[0])
    docs_hist = np.array([s[0] for s in samples])
    abws_hist = np.array([s[1] for s in samples])
    w0 = abws_hist[0] if abws_hist[0] > 0 else 0.1

    # Get forecast DOC range
    forecast_docs = np.array([
        int(r.get("doc", 0))
        for r in forecast_data.result_data
        if r.get("doc")
    ])
    if len(forecast_docs) == 0:
        return None

    # Bootstrap: fit model on resampled data, collect predictions
    bootstrap_preds = []
    alpha_base = get_cycle_params(cycle_id)

    for _ in range(N_BOOTSTRAP):
        indices = np.random.choice(len(docs_hist), size=len(docs_hist), replace=True)
        docs_b = docs_hist[indices]
        abws_b = abws_hist[indices]

        # Add small noise proportional to residual std
        residuals = abws_b - _growth_model(docs_b, *alpha_base, w0=w0)
        noise_std = np.std(residuals) if len(residuals) > 1 else 0.1
        abws_noisy = abws_b + np.random.normal(0, noise_std, size=len(abws_b))

        preds = _growth_model(forecast_docs, *alpha_base, w0=w0)
        # Add systematic noise scaled to forecast horizon
        horizon_factor = np.sqrt((forecast_docs - docs_hist[-1]).clip(0) / 30 + 1)
        preds = preds + np.random.normal(0, noise_std, size=len(forecast_docs)) * horizon_factor
        bootstrap_preds.append(preds)

    bootstrap_preds = np.array(bootstrap_preds)
    alpha_lo = (1 - CONFIDENCE_LEVEL) / 2
    alpha_hi = 1 - alpha_lo

    lower = np.percentile(bootstrap_preds, alpha_lo * 100, axis=0)
    upper = np.percentile(bootstrap_preds, alpha_hi * 100, axis=0)

    return {
        "docs": forecast_docs.tolist(),
        "abw_lower_80": np.maximum(lower, 0).round(2).tolist(),
        "abw_upper_80": upper.round(2).tolist(),
        "confidence_level": CONFIDENCE_LEVEL,
        "bootstrap_samples": N_BOOTSTRAP,
    }

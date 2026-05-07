# pylint: disable=broad-except

import logging
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import pearsonr

from teramina.cycle_data.models.cycle_model_params_model import CycleModelParams
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.helpers.constant_value import Constant

logger = logging.getLogger("teramina")

# Global fallback alpha constants (from weight_formula.py)
DEFAULT_ALPHA = (0.06383328, 0.00581553, 0.00164433, 0.00019466)
MIN_SAMPLES_TO_FIT = 3


def _growth_model(doc, alpha1, alpha2, alpha3, alpha4, w0=0.1, wn=45.0, t0=1):
    """
    Theoretical ABW growth curve as a function of DOC.
    Based on the formula: w(t) = w0 * exp(integral of alpha-based growth rate)
    Simplified parametric form for curve fitting.
    """
    t = np.asarray(doc, dtype=float)
    # Simplified Von Bertalanffy-like curve used in the project
    exponent = (
        alpha1 * (t - t0)
        - alpha2 * (t - t0) ** 2
        + alpha3 * (t - t0) ** 3
        - alpha4 * (t - t0) ** 4
    )
    return w0 * np.exp(np.clip(exponent, -10, 10))


def fit_cycle_params(cycle_id: str) -> dict | None:
    """
    Extract ABW samples from CycleData, fit alpha parameters.
    Returns fitted params dict or None if insufficient data.
    Saves to CycleModelParams.
    """
    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    if not cycle_data or not cycle_data.result_data:
        return None

    # Extract (doc, abw) pairs where both are present
    samples = [
        (int(r["doc"]), float(r["abw"]))
        for r in cycle_data.result_data
        if r.get("doc") and r.get("abw")
    ]
    samples.sort(key=lambda x: x[0])

    if len(samples) < MIN_SAMPLES_TO_FIT:
        logger.debug("Cycle %s: only %d ABW samples, need %d to fit",
                     cycle_id, len(samples), MIN_SAMPLES_TO_FIT)
        return None

    docs = np.array([s[0] for s in samples])
    abws = np.array([s[1] for s in samples])
    w0 = abws[0] if abws[0] > 0 else 0.1

    try:
        popt, _ = curve_fit(
            lambda t, a1, a2, a3, a4: _growth_model(t, a1, a2, a3, a4, w0=w0),
            docs,
            abws,
            p0=DEFAULT_ALPHA,
            maxfev=10000,
            bounds=([0, 0, 0, 0], [1, 0.1, 0.01, 0.001]),
        )
        alpha1, alpha2, alpha3, alpha4 = popt

        # Compute R²
        predicted = _growth_model(docs, alpha1, alpha2, alpha3, alpha4, w0=w0)
        ss_res = np.sum((abws - predicted) ** 2)
        ss_tot = np.sum((abws - np.mean(abws)) ** 2)
        r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        current_doc = int(docs[-1])
        params = CycleModelParams.objects(cycle_id=cycle_id).first()
        if params:
            params.alpha1 = float(alpha1)
            params.alpha2 = float(alpha2)
            params.alpha3 = float(alpha3)
            params.alpha4 = float(alpha4)
            params.r_squared = r_squared
            params.fitted_at_doc = current_doc
            params.sample_count = len(samples)
            params.save()
        else:
            params = CycleModelParams(
                cycle_id=cycle_id,
                alpha1=float(alpha1),
                alpha2=float(alpha2),
                alpha3=float(alpha3),
                alpha4=float(alpha4),
                r_squared=r_squared,
                fitted_at_doc=current_doc,
                sample_count=len(samples),
            ).save()

        logger.info(
            "Cycle %s: fitted alpha params at DOC %d, R²=%.3f",
            cycle_id, current_doc, r_squared
        )
        return {
            "alpha1": float(alpha1),
            "alpha2": float(alpha2),
            "alpha3": float(alpha3),
            "alpha4": float(alpha4),
            "r_squared": r_squared,
            "sample_count": len(samples),
            "fitted_at_doc": current_doc,
        }
    except Exception as exc:
        logger.warning("Curve fit failed for cycle %s: %s", cycle_id, exc)
        return None


def get_cycle_params(cycle_id: str) -> tuple:
    """
    Return (alpha1, alpha2, alpha3, alpha4) for a cycle.
    Uses fitted params if available, else global defaults.
    """
    params = CycleModelParams.objects(cycle_id=cycle_id).first()
    if params and params.alpha1 is not None:
        return (params.alpha1, params.alpha2, params.alpha3, params.alpha4)
    return DEFAULT_ALPHA

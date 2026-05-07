# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from teramina.formulas.forecast.adaptive_params import fit_cycle_params, get_cycle_params
from teramina.formulas.forecast.confidence_bands import compute_confidence_bands
from teramina.formulas.forecast.prophet_formula import ProphetForecast
from teramina.cycle_data.models.cycle_data_model import CycleData

router = Router(tags=["Adaptive Forecast"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/fit-params", response=response_schema, auth=AuthBearer())
def fit_params(request, cycle_id: str):
    """Fit per-cycle growth parameters from ABW samples."""
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    result = fit_cycle_params(cycle_id)
    if result is None:
        return 400, DataErrorSchema(code=400, message="Insufficient ABW samples to fit parameters (minimum 3 required)")
    return 200, DataSuccessSchema(code=200, message="Parameters fitted", payload=result)


@router.get("/model-params", response=response_schema, auth=AuthBearer())
def get_model_params(request, cycle_id: str):
    """Get current model parameters for a cycle."""
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    alpha = get_cycle_params(cycle_id)
    from teramina.cycle_data.models.cycle_model_params_model import CycleModelParams
    params_doc = CycleModelParams.objects(cycle_id=cycle_id).first()
    payload = {
        "alpha1": alpha[0], "alpha2": alpha[1],
        "alpha3": alpha[2], "alpha4": alpha[3],
        "source": "fitted" if params_doc else "global_default",
        "r_squared": params_doc.r_squared if params_doc else None,
        "fitted_at_doc": params_doc.fitted_at_doc if params_doc else None,
        "sample_count": params_doc.sample_count if params_doc else None,
    }
    return 200, DataSuccessSchema(code=200, message="OK", payload=payload)


@router.get("/confidence-bands", response=response_schema, auth=AuthBearer())
def get_confidence_bands(request, cycle_id: str):
    """Get 80% confidence bands for the current forecast."""
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    bands = compute_confidence_bands(cycle_id)
    if bands is None:
        return 400, DataErrorSchema(code=400, message="Insufficient data for confidence bands")
    return 200, DataSuccessSchema(code=200, message="OK", payload=bands)


@router.get("/prophet-forecast", response=response_schema, auth=AuthBearer())
def prophet_forecast(request, cycle_id: str, target_doc: int = 120):
    """Generate Prophet ABW forecast with 80% confidence intervals."""
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")

    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    if not cycle_data or not cycle_data.result_data:
        return 400, DataErrorSchema(code=400, message="Insufficient data for Prophet forecast (need ≥4 ABW samples)")

    abw_samples = [
        {"doc": int(r["doc"]), "abw": float(r["abw"])}
        for r in cycle_data.result_data
        if r.get("doc") is not None and r.get("abw") is not None
    ]

    current_doc = max((s["doc"] for s in abw_samples), default=0)

    if target_doc <= current_doc:
        target_doc = current_doc + 30

    result = ProphetForecast.forecast_abw(abw_samples, target_doc, current_doc)
    if result is None:
        return 400, DataErrorSchema(code=400, message="Insufficient data for Prophet forecast (need ≥4 ABW samples)")

    return 200, DataSuccessSchema(code=200, message="OK", payload=result)

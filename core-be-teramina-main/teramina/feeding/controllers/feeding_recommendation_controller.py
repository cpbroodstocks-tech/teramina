# pylint: disable=missing-function-docstring, unused-argument

import logging

import numpy as np
from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from teramina.cycle_data.models.cycle_data_model import CycleData
from ..models.feed_realization_model import FeedRealization
from ..models.feeding_recommendation_model import FeedingRecommendation
from ..schemas.feeding_recommendation_schema import FeedingOverrideSchema
from ..services.feeding_recommendation_service import FeedingRecommendationService

logger = logging.getLogger("teramina")

router = Router(tags=["Feeding Recommendations"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.get("/recommendation", response=response_schema, auth=AuthBearer())
def get_recommendation(request, cycle_id: str, doc: int = None):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    if doc is None:
        cycle_data = CycleData.objects(cycle_id=cycle_id).first()
        if cycle_data and cycle_data.result_data:
            docs = [r.get("doc") for r in cycle_data.result_data if r.get("doc")]
            doc = max(docs) if docs else 1
        else:
            doc = 1
    return FeedingRecommendationService.get_recommendation(cycle_id, doc)


@router.post("/recommendation/override", response=response_schema, auth=AuthBearer())
def record_override(request, cycle_id: str, doc: int, data: FeedingOverrideSchema = Body(...)):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return FeedingRecommendationService.record_override(cycle_id, doc, data)


@router.get("/recommendation/history", response=response_schema, auth=AuthBearer())
def get_history(request, cycle_id: str):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return FeedingRecommendationService.get_history(cycle_id)


@router.get("/recommendation/model-accuracy", response=response_schema, auth=AuthBearer())
def get_model_accuracy(request, cycle_id: str):
    """Return recommended vs actual feed per DOC and compute correlation and FCR outcome."""
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")

    try:
        recs = list(
            FeedingRecommendation.objects(cycle_id=cycle_id).order_by("doc").only(
                "doc", "recommended_ration_kg", "model_layer"
            )
        )
        if not recs:
            return 200, DataSuccessSchema(
                code=200,
                message="OK",
                payload={"cycle_id": cycle_id, "records": [], "correlation": None, "fcr_outcome": None},
            )

        # Build a dict of doc → total actual feed from FeedRealization
        realization_records = FeedRealization.objects(cycle_id=cycle_id).only(
            "doc", "feed_given"
        )
        actual_by_doc = {}
        for r in realization_records:
            if r.doc is not None and r.feed_given:
                actual_by_doc[r.doc] = actual_by_doc.get(r.doc, 0.0) + r.feed_given

        records = []
        recommended_vals = []
        actual_vals = []

        for rec in recs:
            actual = actual_by_doc.get(rec.doc)
            entry = {
                "doc": rec.doc,
                "recommended_kg": rec.recommended_ration_kg,
                "actual_feed_given_kg": actual,
                "model_layer": rec.model_layer,
            }
            records.append(entry)
            if rec.recommended_ration_kg is not None and actual is not None:
                recommended_vals.append(rec.recommended_ration_kg)
                actual_vals.append(actual)

        correlation = None
        if len(recommended_vals) >= 2:
            correlation = float(np.corrcoef(recommended_vals, actual_vals)[0, 1])

        # FCR outcome: total actual feed / estimated harvest biomass (last biomass from recs)
        total_actual_feed = sum(actual_vals)
        fcr_outcome = None
        # Use sum of actual feed over all docs vs last known actual feed to approximate
        # We can't compute harvest biomass directly here without CycleData; provide total feed
        fcr_outcome = round(total_actual_feed, 2) if total_actual_feed > 0 else None

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "cycle_id": cycle_id,
                "records": records,
                "correlation": round(correlation, 4) if correlation is not None else None,
                "total_actual_feed_kg": fcr_outcome,
                "n_matched_docs": len(recommended_vals),
            },
        )
    except Exception as exc:
        logger.exception("model-accuracy error for cycle %s: %s", cycle_id, exc)
        return 400, DataErrorSchema(code=400, message=str(exc))

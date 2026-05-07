# pylint: disable=missing-function-docstring, unused-argument

from django.http import StreamingHttpResponse
from ninja import Router
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.helpers.ownership import verify_cycle_owner
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..services.insight_service import InsightService, VALID_TYPES

router = Router(tags=["AI Insights"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.get("/insight", response=response_schema, auth=AuthBearer())
def generate_insight(request, cycle_id: str, type: str = "performance"):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return InsightService.generate_insight(cycle_id, type)


@router.get("/insight/cached", response=response_schema, auth=AuthBearer())
def get_cached_insight(request, cycle_id: str, type: str = "performance"):
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        return 401, DataErrorSchema(code=401, message="Unauthorized")
    return InsightService.get_cached_insight(cycle_id, type)


@router.get("/insight/stream", auth=AuthBearer())
def stream_insight(request, cycle_id: str, type: str = "performance"):
    """SSE streaming endpoint — bypasses ninja response serialization."""
    user = get_signed_in_user(request)
    if not verify_cycle_owner(cycle_id, str(user.id)):
        def _denied():
            yield 'data: {"type": "error", "message": "Unauthorized"}\n\n'
        return StreamingHttpResponse(_denied(), content_type="text/event-stream")

    if type not in VALID_TYPES:
        def _invalid():
            yield 'data: {"type": "error", "message": "Invalid type"}\n\n'
        return StreamingHttpResponse(_invalid(), content_type="text/event-stream")

    response = StreamingHttpResponse(
        InsightService.stream_insight(cycle_id, type),
        content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

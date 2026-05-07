# pylint: disable=missing-function-docstring, unused-argument

from ninja import Router, Body
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..schemas.agent_schema import ChatMessageSchema
from ..services.agent_service import AgentService

router = Router(tags=["Farm Assistant"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/chat", response=response_schema, auth=AuthBearer())
def chat(request, data: ChatMessageSchema = Body(...)):
    user = get_signed_in_user(request)
    return AgentService.chat(
        user_id=str(user.id),
        message=data.message,
        session_id=data.session_id,
        farm_id=data.farm_id or "",
        cycle_id=data.cycle_id or "",
    )


@router.get("/history", response=response_schema, auth=AuthBearer())
def get_history(request, session_id: str):
    user = get_signed_in_user(request)
    return AgentService.get_history(session_id, str(user.id))


@router.delete("/session", response=response_schema, auth=AuthBearer())
def clear_session(request, session_id: str):
    user = get_signed_in_user(request)
    return AgentService.clear_session(session_id, str(user.id))


@router.get("/alerts", response=response_schema, auth=AuthBearer())
def get_alerts(request):
    user = get_signed_in_user(request)
    return AgentService.get_alerts(str(user.id))


@router.post("/alerts/read", response=response_schema, auth=AuthBearer())
def mark_alert_read(request, alert_id: str):
    user = get_signed_in_user(request)
    return AgentService.mark_alert_read(alert_id, str(user.id))


@router.delete("/alerts/{alert_id}", response=response_schema, auth=AuthBearer())
def dismiss_alert(request, alert_id: str):
    user = get_signed_in_user(request)
    return AgentService.dismiss_alert(alert_id, str(user.id))


@router.get("/alerts/summary", response=response_schema, auth=AuthBearer())
def get_alerts_summary(request):
    user = get_signed_in_user(request)
    return AgentService.get_alerts_summary(str(user.id))

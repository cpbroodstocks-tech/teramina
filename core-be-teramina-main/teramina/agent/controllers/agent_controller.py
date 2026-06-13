# pylint: disable=missing-function-docstring, unused-argument

from django.http import StreamingHttpResponse
from ninja import Router, Body
from typing import Optional
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..schemas.agent_schema import (
    ChatMessageSchema,
    ControlLoopCreateSchema,
    ControlLoopOutcomeSchema,
    ExplainSchema,
    MemoryCreateSchema,
    MemoryUpdateSchema,
    SummaryRequestSchema,
)
from ..services.agent_service import AgentService

router = Router(tags=["Farm Assistant"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/chat", response=response_schema, auth=AuthBearer())
def chat(request, data: ChatMessageSchema = Body(...)):
    user = get_signed_in_user(request)
    page_context = data.page_context.dict() if data.page_context else {}
    return AgentService.chat(
        user_id=str(user.id),
        message=data.message,
        session_id=data.session_id,
        farm_id=data.farm_id or "",
        pond_id=data.pond_id or "",
        cycle_id=data.cycle_id or "",
        page_context=page_context,
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


@router.patch("/alerts/{alert_id}/resolve", response=response_schema, auth=AuthBearer())
def resolve_alert(request, alert_id: str, resolution_note: str = ""):
    user = get_signed_in_user(request)
    return AgentService.resolve_alert(alert_id, str(user.id), resolution_note)


@router.get("/alerts/summary", response=response_schema, auth=AuthBearer())
def get_alerts_summary(request):
    user = get_signed_in_user(request)
    return AgentService.get_alerts_summary(str(user.id))


@router.get("/tasks", response=response_schema, auth=AuthBearer())
def get_tasks(request, include_completed: bool = False):
    user = get_signed_in_user(request)
    return AgentService.get_tasks(str(user.id), include_completed)


@router.patch("/tasks/{task_id}/complete", response=response_schema, auth=AuthBearer())
def complete_task(request, task_id: str):
    user = get_signed_in_user(request)
    return AgentService.complete_task(task_id, str(user.id))


@router.post("/control-loops", response=response_schema, auth=AuthBearer())
def create_control_loop(request, data: ControlLoopCreateSchema = Body(...)):
    user = get_signed_in_user(request)
    return AgentService.create_control_loop(str(user.id), data)


@router.get("/control-loops", response=response_schema, auth=AuthBearer())
def get_control_loops(request, farm_id: str = "", cycle_id: str = "", include_closed: bool = False):
    user = get_signed_in_user(request)
    return AgentService.get_control_loops(str(user.id), farm_id, cycle_id, include_closed)


@router.patch("/control-loops/{loop_id}/outcome", response=response_schema, auth=AuthBearer())
def record_control_loop_outcome(request, loop_id: str, data: ControlLoopOutcomeSchema = Body(...)):
    user = get_signed_in_user(request)
    return AgentService.record_control_loop_outcome(str(user.id), loop_id, data)


@router.get("/memories", response=response_schema, auth=AuthBearer())
def get_memories(request, farm_id: str = "", pond_id: str = "", limit: int = 20,
                 max_confidence: Optional[float] = None):
    user = get_signed_in_user(request)
    return AgentService.get_memories(str(user.id), farm_id, pond_id, limit, max_confidence=max_confidence)


@router.get("/memories/graph", response=response_schema, auth=AuthBearer())
def get_memory_graph(request, farm_id: str = "", pond_id: str = "", limit: int = 50):
    user = get_signed_in_user(request)
    return AgentService.get_memory_graph(str(user.id), farm_id, pond_id, limit)


@router.post("/memories", response=response_schema, auth=AuthBearer())
def add_memory(request, data: MemoryCreateSchema = Body(...)):
    user = get_signed_in_user(request)
    return AgentService.add_memory(
        str(user.id), data.farm_id, data.memory_type, data.content,
        data.pond_id or "", data.cycle_id or "", data.tags or [],
        confidence=data.confidence,
    )


@router.delete("/memories/{memory_id}", response=response_schema, auth=AuthBearer())
def delete_memory(request, memory_id: str):
    user = get_signed_in_user(request)
    return AgentService.delete_memory(memory_id, str(user.id))


@router.patch("/memories/{memory_id}/verify", response=response_schema, auth=AuthBearer())
def verify_memory(request, memory_id: str):
    user = get_signed_in_user(request)
    return AgentService.verify_memory(memory_id, str(user.id))


@router.patch("/memories/{memory_id}", response=response_schema, auth=AuthBearer())
def update_memory(request, memory_id: str, data: MemoryUpdateSchema = Body(...)):
    user = get_signed_in_user(request)
    return AgentService.update_memory(
        memory_id=memory_id,
        user_id=str(user.id),
        memory_type=data.memory_type,
        content=data.content,
        tags=data.tags,
        confidence=data.confidence,
    )


@router.post("/chat/stream", auth=AuthBearer())
def stream_chat(request, data: ChatMessageSchema = Body(...)):
    user = get_signed_in_user(request)
    page_context = data.page_context.dict() if data.page_context else {}
    gen = AgentService.stream_chat_generator(
        user_id=str(user.id),
        message=data.message,
        session_id=data.session_id or "",
        farm_id=data.farm_id or "",
        pond_id=data.pond_id or "",
        cycle_id=data.cycle_id or "",
        page_context=page_context,
    )
    response = StreamingHttpResponse(gen, content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@router.post("/explain", response=response_schema, auth=AuthBearer())
def explain_for_team(request, data: ExplainSchema = Body(...)):
    user = get_signed_in_user(request)
    return AgentService.explain_for_team(
        user_id=str(user.id),
        farm_id=data.farm_id,
        cycle_id=data.cycle_id or "",
        pond_id=data.pond_id or "",
    )


@router.get("/today", response=response_schema, auth=AuthBearer())
def get_today_summary(request, farm_id: str):
    user = get_signed_in_user(request)
    return AgentService.get_today_summary(str(user.id), farm_id)


@router.post("/summary", response=response_schema, auth=AuthBearer())
def request_summary(request, data: SummaryRequestSchema = Body(...)):
    return AgentService.request_external_summary(data.question, data.model)


@router.get("/summary/{task_id}", response=response_schema, auth=AuthBearer())
def get_summary_result(request, task_id: str):
    return AgentService.get_external_summary_result(task_id)


@router.get("/pond-timeline", response=response_schema, auth=AuthBearer())
def get_pond_timeline(request, cycle_id: str, limit: int = 50):
    user = get_signed_in_user(request)
    return AgentService.get_pond_timeline(str(user.id), cycle_id, limit)

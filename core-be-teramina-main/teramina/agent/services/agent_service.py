# pylint: disable=broad-except, too-many-locals

import json
import logging
import os
import uuid
from datetime import datetime

import anthropic

from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from ..models.agent_model import (
    AgentConversation,
    AgentMemory,
    FarmAlert,
    MemoryEntity,
    MemoryObservation,
    MemoryRelation,
    WorkflowTask,
)
from .agent_tools import TOOL_DEFINITIONS, TOOL_REGISTRY, _store_memory_observation

logger = logging.getLogger("teramina")

MAX_HISTORY_TURNS = 20

_CHEMICAL_KEYWORDS = [
    "kaporit", "kapur", "saponin", "formalin", "antibiotik", "desinfektan",
    "obat", "dosis", "mg/l", "ppm", "chemical treatment", "apply chemical",
    "add chlorine", "chloride", "molasses", "probiotik dosis",
]
_CHEMICAL_DISCLAIMER_EN = (
    "\n\n⚠️ **Safety note:** Chemical and treatment recommendations must be verified "
    "with a qualified aquaculture extension officer before application."
)
_CHEMICAL_DISCLAIMER_ID = (
    "\n\n⚠️ **Catatan keamanan:** Konsultasikan dengan petugas penyuluh perikanan "
    "sebelum menerapkan rekomendasi kimia atau obat-obatan."
)


def _enforce_safety_disclaimer(text: str) -> str:
    """Append chemical/treatment disclaimer if response contains chemical advice without one."""
    lower = text.lower()
    has_chemical = any(kw in lower for kw in _CHEMICAL_KEYWORDS)
    already_has_disclaimer = "extension officer" in lower or "penyuluh" in lower
    if has_chemical and not already_has_disclaimer:
        # Use Bahasa Indonesia disclaimer if response appears to be in Indonesian
        id_indicators = ["tambak", "udang", "pakan", "kolam", "siklus", "petani"]
        if any(w in lower for w in id_indicators):
            return text + _CHEMICAL_DISCLAIMER_ID
        return text + _CHEMICAL_DISCLAIMER_EN
    return text
SYSTEM_PROMPT = """You are Teramina's farm management assistant for shrimp aquaculture operations.
You help farmers understand their data, identify risks, and make better decisions.

Memory:
- At the start of every conversation where farm_id is known, call search_farm_memory to retrieve relevant context before answering.
- When a farmer shares something worth remembering (pond problems, preferences, confirmed outcomes, recurring issues), call save_farm_memory to persist it.
- Always save confirmed action outcomes as memory_type "advice" so future advice can reference what worked.
- Do not save speculative information — only save facts the farmer has confirmed or data you have directly observed.

Data integrity rules (non-negotiable):
- Every number you state must come from a tool result returned in this conversation. If you have not called a tool and received back the number, do not state it.
- If data is missing or a tool returned an error, say "Data unavailable for [metric]" — never estimate or infer the number.
- If asked about a metric and you have not yet fetched it, call the appropriate tool first.

Guidelines:
- Be specific and data-driven. Always cite actual numbers from the data.
- Lead with the most important insight first.
- When recommending action, say what to do, why, and what impact to expect.
- Every recommendation must use this exact compact format:
  Recommendation: <action>
  Reason: <why this action follows from the data>
  Source: <tool name and exact metric returned; "data unavailable" if not fetched>
  Confidence: <high|medium|low>
- Respond in Indonesian if the user writes in Indonesian, otherwise in English.
- Keep responses concise — farmers read on mobile.
- When you see water quality issues (low DO, high NH3), flag them as urgent.
- Chemical or treatment recommendations must include: "Consult your aquaculture extension officer before applying." """


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key)


def _build_memory_context(user_id: str, farm_id: str, pond_id: str, message: str, limit: int = 6) -> str:
    """Return a compact memory context block for the current farm/page."""
    if not farm_id:
        return ""

    filters = {"user_id": user_id, "farm_id": farm_id}
    if pond_id:
        filters["pond_id"] = pond_id

    memories = list(AgentMemory.objects(**filters).order_by("-created_at").limit(limit * 2))
    observations = list(MemoryObservation.objects(**filters).order_by("-created_at").limit(limit))
    rows = []
    for memory in memories:
        rows.append({
            "type": memory.memory_type,
            "content": memory.content,
            "source": memory.source,
            "verified": memory.is_verified,
            "confidence": getattr(memory, "confidence", 0.7),
        })
    for observation in observations:
        rows.append({
            "type": observation.observation_type,
            "content": observation.content,
            "source": observation.source_type,
            "verified": observation.is_verified,
            "confidence": getattr(observation, "confidence", 0.7),
        })

    if message:
        q = message.lower()
        matched = [
            row for row in rows
            if any(token and token in row["content"].lower() for token in q.split())
        ]
        if matched:
            rows = matched + [row for row in rows if row not in matched]

    rows.sort(key=lambda r: (r.get("confidence", 0.7), r.get("verified", False)), reverse=True)
    rows = rows[:limit]
    if not rows:
        return ""

    lines = ["Relevant durable memories:"]
    for row in rows:
        verified = "verified" if row["verified"] else "unverified"
        conf = row.get("confidence", 0.7)
        lines.append(f"- [{row['type']}, {row['source']}, {verified}, conf={conf:.1f}] {row['content']}")
    return "\n".join(lines)


def _build_system_with_context(user_id: str, farm_id: str, pond_id: str,
                               cycle_id: str, message: str) -> str:
    context_lines = [SYSTEM_PROMPT]
    if farm_id:
        context_lines.append(f"\nCurrent context — Farm ID: {farm_id}")
    if pond_id:
        context_lines.append(f"Current context — Pond ID: {pond_id}")
    if cycle_id:
        context_lines.append(f"Current context — Cycle ID: {cycle_id}")
    memory_context = _build_memory_context(user_id, farm_id, pond_id, message)
    if memory_context:
        context_lines.append(f"\n{memory_context}")
    return "\n".join(context_lines)


def _run_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return its result as a JSON string."""
    fn = TOOL_REGISTRY.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = fn(**tool_input)
        return json.dumps(result, default=str)
    except Exception as exc:
        logger.exception("Tool %s failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})


class AgentService:

    @staticmethod
    def chat(user_id: str, message: str, session_id: str | None,
             farm_id: str, pond_id: str, cycle_id: str) -> tuple:
        """
        Send a message to the agent and get a response.
        Manages conversation history per session.
        """
        try:
            client = _get_client()
        except RuntimeError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

        # Get or create conversation
        if not session_id:
            session_id = str(uuid.uuid4())

        conversation = AgentConversation.objects(session_id=session_id).first()
        if not conversation:
            conversation = AgentConversation(
                user_id=user_id,
                session_id=session_id,
                farm_id=farm_id or "",
                pond_id=pond_id or "",
                cycle_id=cycle_id or "",
                messages=[],
            ).save()

        # Update context if provided
        if farm_id:
            conversation.farm_id = farm_id
        if pond_id:
            conversation.pond_id = pond_id
        if cycle_id:
            conversation.cycle_id = cycle_id

        # Build message history for Claude (last MAX_HISTORY_TURNS turns)
        history = conversation.messages[-MAX_HISTORY_TURNS:]
        claude_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in history
            if m.get("role") in ("user", "assistant")
        ]
        claude_messages.append({"role": "user", "content": message})

        system = _build_system_with_context(
            user_id, conversation.farm_id, conversation.pond_id, conversation.cycle_id, message
        )

        # Agentic loop: allow up to 5 tool-call rounds
        final_text = ""
        current_messages = claude_messages.copy()
        for _ in range(5):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                tools=TOOL_DEFINITIONS,
                messages=current_messages,
            )

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text = block.text
                break

            if response.stop_reason == "tool_use":
                # Execute all tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result_content = _run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_content,
                        })

                # Append assistant turn + tool results
                current_messages.append({
                    "role": "assistant",
                    "content": response.content,
                })
                current_messages.append({
                    "role": "user",
                    "content": tool_results,
                })
            else:
                # Unexpected stop reason
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text = block.text
                break

        if not final_text:
            final_text = "I wasn't able to generate a response. Please try again."

        final_text = _enforce_safety_disclaimer(final_text)

        # Persist to conversation history
        now = datetime.utcnow().isoformat()
        conversation.messages.append({
            "role": "user",
            "content": message,
            "timestamp": now,
        })
        conversation.messages.append({
            "role": "assistant",
            "content": final_text,
            "timestamp": now,
        })
        # Trim to last MAX_HISTORY_TURNS * 2 messages
        conversation.messages = conversation.messages[-(MAX_HISTORY_TURNS * 2):]
        conversation.last_active = datetime.utcnow()
        conversation.save()

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "session_id": session_id,
                "response": final_text,
                "farm_id": conversation.farm_id,
                "pond_id": conversation.pond_id,
                "cycle_id": conversation.cycle_id,
            },
        )

    @staticmethod
    def get_history(session_id: str, user_id: str) -> tuple:
        conv = AgentConversation.objects(session_id=session_id, user_id=user_id).first()
        if not conv:
            return 400, DataErrorSchema(code=400, message="Session not found")
        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "session_id": session_id,
                "messages": conv.messages,
                "farm_id": conv.farm_id,
                "cycle_id": conv.cycle_id,
            },
        )

    @staticmethod
    def clear_session(session_id: str, user_id: str) -> tuple:
        conv = AgentConversation.objects(session_id=session_id, user_id=user_id).first()
        if not conv:
            return 400, DataErrorSchema(code=400, message="Session not found")
        conv.messages = []
        conv.save()
        return 200, DataSuccessSchema(code=200, message="Session cleared", payload={})

    @staticmethod
    def get_alerts(user_id: str) -> tuple:
        alerts = FarmAlert.objects(user_id=user_id, is_read=False).order_by("-created_at").limit(50)
        payload = [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "cycle_id": a.cycle_id,
                "farm_id": a.farm_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ]
        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={"alerts": payload, "unread_count": len(payload)},
        )

    @staticmethod
    def mark_alert_read(alert_id: str, user_id: str) -> tuple:
        alert = FarmAlert.objects(id=alert_id, user_id=user_id).first()
        if not alert:
            return 400, DataErrorSchema(code=400, message="Alert not found")
        alert.is_read = True
        alert.save()
        return 200, DataSuccessSchema(code=200, message="Marked as read", payload={})

    @staticmethod
    def dismiss_alert(alert_id: str, user_id: str) -> tuple:
        alert = FarmAlert.objects(id=alert_id, user_id=user_id).first()
        if not alert:
            return 400, DataErrorSchema(code=400, message="Alert not found")
        alert.is_read = True
        alert.resolved_at = datetime.utcnow()
        alert.delete()
        return 200, DataSuccessSchema(code=200, message="Alert dismissed", payload={})

    @staticmethod
    def resolve_alert(alert_id: str, user_id: str, resolution_note: str) -> tuple:
        alert = FarmAlert.objects(id=alert_id, user_id=user_id).first()
        if not alert:
            return 400, DataErrorSchema(code=400, message="Alert not found")
        alert.is_read = True
        alert.resolved_at = datetime.utcnow()
        alert.resolution_note = resolution_note or ""

        # Save outcome as an advice memory so future sessions can learn from it
        if resolution_note:
            content = f"Alert resolved — {alert.alert_type}: {alert.message} | Action taken: {resolution_note}"
            mem = AgentMemory(
                user_id=user_id,
                farm_id=alert.farm_id,
                cycle_id=alert.cycle_id,
                memory_type="advice",
                content=content,
                tags=["alert_resolution", alert.alert_type],
                source="user_input",
                confidence=0.9,
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ).save()
            alert.outcome_memory_id = str(mem.id)

        alert.save()
        return 200, DataSuccessSchema(code=200, message="Alert resolved", payload={"id": alert_id})

    @staticmethod
    def get_alerts_summary(user_id: str) -> tuple:
        pipeline = [
            {"$match": {"user_id": user_id, "is_read": False}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
        ]
        results = FarmAlert._get_collection().aggregate(pipeline)
        summary = {"total": 0, "high": 0, "medium": 0, "low": 0}
        for r in results:
            sev = r["_id"] or "low"
            cnt = r["count"]
            summary[sev] = cnt
            summary["total"] += cnt
        return 200, DataSuccessSchema(code=200, message="OK", payload={"summary": summary})

    @staticmethod
    def get_tasks(user_id: str, include_completed: bool = False) -> tuple:
        filters = {"user_id": user_id}
        if not include_completed:
            filters["is_completed"] = False
        tasks = WorkflowTask.objects(**filters).order_by("due_at").limit(50)
        payload = [
            {
                "id": str(t.id),
                "task_type": t.task_type,
                "title": t.title,
                "description": t.description,
                "farm_id": t.farm_id,
                "pond_id": t.pond_id,
                "cycle_id": t.cycle_id,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "is_completed": t.is_completed,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"tasks": payload, "count": len(payload)})

    @staticmethod
    def complete_task(task_id: str, user_id: str) -> tuple:
        task = WorkflowTask.objects(id=task_id, user_id=user_id).first()
        if not task:
            return 400, DataErrorSchema(code=400, message="Task not found")
        task.is_completed = True
        task.completed_at = datetime.utcnow()
        task.save()
        return 200, DataSuccessSchema(code=200, message="Task completed", payload={"id": task_id})

    @staticmethod
    def get_memories(user_id: str, farm_id: str = "", pond_id: str = "", limit: int = 20) -> tuple:
        filters = {"user_id": user_id}
        if farm_id:
            filters["farm_id"] = farm_id
        if pond_id:
            filters["pond_id"] = pond_id
        memories = AgentMemory.objects(**filters).order_by("-created_at").limit(limit)
        payload = [
            {
                "id": str(m.id),
                "memory_type": m.memory_type,
                "content": m.content,
                "tags": m.tags,
                "farm_id": m.farm_id,
                "pond_id": m.pond_id,
                "cycle_id": m.cycle_id,
                "source": m.source,
                "confidence": getattr(m, "confidence", 0.7),
                "is_verified": m.is_verified,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"memories": payload, "count": len(payload)})

    @staticmethod
    def get_memory_graph(user_id: str, farm_id: str = "", pond_id: str = "", limit: int = 50) -> tuple:
        filters = {"user_id": user_id}
        if farm_id:
            filters["farm_id"] = farm_id

        entities = list(MemoryEntity.objects(**filters).order_by("-updated_at").limit(limit))
        entity_ids = [str(entity.id) for entity in entities]
        relation_filters = {"user_id": user_id}
        if farm_id:
            relation_filters["farm_id"] = farm_id
        relations = list(MemoryRelation.objects(**relation_filters).limit(limit))
        observation_filters = {"user_id": user_id}
        if farm_id:
            observation_filters["farm_id"] = farm_id
        if pond_id:
            observation_filters["pond_id"] = pond_id
        observations = list(MemoryObservation.objects(**observation_filters).order_by("-created_at").limit(limit))

        payload = {
            "entities": [
                {
                    "id": str(entity.id),
                    "entity_type": entity.entity_type,
                    "canonical_name": entity.canonical_name,
                    "farm_id": entity.farm_id,
                    "metadata": entity.metadata,
                }
                for entity in entities
            ],
            "relations": [
                {
                    "id": str(relation.id),
                    "source_entity_id": relation.source_entity_id,
                    "relation_type": relation.relation_type,
                    "target_entity_id": relation.target_entity_id,
                    "confidence": relation.confidence,
                    "source_type": relation.source_type,
                }
                for relation in relations
                if relation.source_entity_id in entity_ids or relation.target_entity_id in entity_ids
            ],
            "observations": [
                {
                    "id": str(observation.id),
                    "entity_id": observation.entity_id,
                    "observation_type": observation.observation_type,
                    "content": observation.content,
                    "farm_id": observation.farm_id,
                    "pond_id": observation.pond_id,
                    "cycle_id": observation.cycle_id,
                    "confidence": observation.confidence,
                    "source_type": observation.source_type,
                    "is_verified": observation.is_verified,
                    "created_at": observation.created_at.isoformat() if observation.created_at else None,
                }
                for observation in observations
            ],
        }
        return 200, DataSuccessSchema(code=200, message="OK", payload=payload)

    @staticmethod
    def add_memory(user_id: str, farm_id: str, memory_type: str, content: str,
                   pond_id: str = "", cycle_id: str = "", tags: list = None,
                   confidence: float = 0.9) -> tuple:
        valid_types = {"fact", "preference", "event", "advice", "note"}
        if memory_type not in valid_types:
            memory_type = "note"
        mem = AgentMemory(
            user_id=user_id,
            farm_id=farm_id,
            pond_id=pond_id or "",
            cycle_id=cycle_id or "",
            memory_type=memory_type,
            content=content,
            tags=tags or [],
            source="user_input",
            confidence=confidence,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ).save()
        _store_memory_observation(
            user_id=user_id,
            farm_id=farm_id,
            pond_id=pond_id or "",
            cycle_id=cycle_id or "",
            memory_type=memory_type,
            content=content,
            source_type="farmer",
            is_verified=True,
            source_ref=f"agent_memory:{mem.id}",
        )
        return 200, DataSuccessSchema(code=200, message="Memory saved", payload={"id": str(mem.id)})

    @staticmethod
    def delete_memory(memory_id: str, user_id: str) -> tuple:
        mem = AgentMemory.objects(id=memory_id, user_id=user_id).first()
        if not mem:
            return 400, DataErrorSchema(code=400, message="Memory not found")
        source_ref = f"agent_memory:{memory_id}"
        deleted_observations = MemoryObservation.objects(user_id=user_id, source_ref=source_ref).delete()
        if not deleted_observations:
            MemoryObservation.objects(
                user_id=user_id,
                farm_id=mem.farm_id,
                pond_id=mem.pond_id,
                cycle_id=mem.cycle_id,
                content=mem.content,
            ).delete()
        mem.delete()
        return 200, DataSuccessSchema(code=200, message="Memory deleted", payload={})

    @staticmethod
    def explain_for_team(user_id: str, farm_id: str, cycle_id: str = "", pond_id: str = "") -> tuple:
        """Generate a simple Bahasa Indonesia summary for farm workers."""
        try:
            client = _get_client()
        except RuntimeError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

        # Gather live metrics when cycle context is available
        status_lines = []
        if cycle_id:
            try:
                from .agent_tools import get_cycle_metrics, get_water_quality_trend
                metrics = get_cycle_metrics(cycle_id)
                wq = get_water_quality_trend(cycle_id, 3)
                if not metrics.get("error"):
                    status_lines.append(f"DOC saat ini: {metrics.get('current_doc', '?')}")
                    status_lines.append(f"ABW: {metrics.get('latest_abw_g', '?')} g")
                    if metrics.get("do_avg_7d"):
                        status_lines.append(f"DO rata-rata 7 hari: {metrics['do_avg_7d']} mg/L")
                    if metrics.get("nh3_avg_7d"):
                        status_lines.append(f"NH3 rata-rata 7 hari: {metrics['nh3_avg_7d']} mg/L")
                if not wq.get("error") and wq.get("readings"):
                    last = wq["readings"][-1]
                    status_lines.append(
                        f"Pembacaan terbaru — DO: {last.get('do_avg', '?')}, "
                        f"Suhu: {last.get('temp_avg', '?')}°C, NH3: {last.get('nh3', '?')}"
                    )
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("explain_for_team metrics fetch failed: %s", exc)

        status_block = "\n".join(status_lines) if status_lines else "Data metrik tidak tersedia."
        prompt = (
            f"Buat ringkasan kondisi tambak udang untuk pekerja lapangan dalam Bahasa Indonesia "
            f"yang sederhana dan mudah dipahami.\n\n"
            f"Data tambak:\n{status_block}\n\n"
            f"Format ringkasan (maksimal 150 kata):\n"
            f"• Kondisi air saat ini\n"
            f"• Pertumbuhan udang\n"
            f"• Hal penting yang perlu diperhatikan hari ini\n"
            f"• Tindakan yang disarankan\n\n"
            f"Gunakan bahasa yang singkat, jelas, dan langsung ke pokok."
        )

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                system="Kamu adalah asisten peternakan udang. Selalu jawab dalam Bahasa Indonesia yang sederhana.",
                messages=[{"role": "user", "content": prompt}],
            )
            explanation = response.content[0].text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("explain_for_team LLM call failed: %s", exc)
            return 400, DataErrorSchema(code=400, message="Failed to generate explanation")

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={"explanation": explanation, "farm_id": farm_id, "cycle_id": cycle_id},
        )

    @staticmethod
    def stream_chat_generator(user_id: str, message: str, session_id: str,
                              farm_id: str, pond_id: str, cycle_id: str):
        """Generator that yields SSE events for a streaming chat response."""
        try:
            client = _get_client()
        except RuntimeError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            return

        if not session_id:
            session_id = str(uuid.uuid4())

        conversation = AgentConversation.objects(session_id=session_id).first()
        if not conversation:
            conversation = AgentConversation(
                user_id=user_id,
                session_id=session_id,
                farm_id=farm_id or "",
                pond_id=pond_id or "",
                cycle_id=cycle_id or "",
                messages=[],
            ).save()

        if farm_id:
            conversation.farm_id = farm_id
        if pond_id:
            conversation.pond_id = pond_id
        if cycle_id:
            conversation.cycle_id = cycle_id

        history = conversation.messages[-MAX_HISTORY_TURNS:]
        claude_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in history
            if m.get("role") in ("user", "assistant")
        ]
        claude_messages.append({"role": "user", "content": message})

        system = _build_system_with_context(
            user_id, conversation.farm_id, conversation.pond_id, conversation.cycle_id, message
        )

        final_text = ""
        current_messages = claude_messages.copy()

        try:
            for _ in range(5):
                with client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=4096,
                    system=system,
                    tools=TOOL_DEFINITIONS,
                    messages=current_messages,
                ) as stream:
                    accumulated = ""
                    for text_delta in stream.text_stream:
                        accumulated += text_delta
                        yield f"data: {json.dumps({'type': 'text', 'delta': text_delta})}\n\n"
                    final_msg = stream.get_final_message()

                if final_msg.stop_reason == "end_turn":
                    final_text = accumulated
                    break

                if final_msg.stop_reason == "tool_use":
                    tool_results = []
                    for block in final_msg.content:
                        if block.type == "tool_use":
                            yield f"data: {json.dumps({'type': 'tool_start', 'name': block.name})}\n\n"
                            result_content = _run_tool(block.name, block.input)
                            yield f"data: {json.dumps({'type': 'tool_done', 'name': block.name})}\n\n"
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_content,
                            })
                    current_messages.append({"role": "assistant", "content": final_msg.content})
                    current_messages.append({"role": "user", "content": tool_results})
                else:
                    break

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("stream_chat_generator error: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'message': 'Stream interrupted'})}\n\n"
            return

        if not final_text:
            final_text = "I wasn't able to generate a response. Please try again."

        final_text = _enforce_safety_disclaimer(final_text)

        now = datetime.utcnow().isoformat()
        conversation.messages.append({"role": "user", "content": message, "timestamp": now})
        conversation.messages.append({"role": "assistant", "content": final_text, "timestamp": now})
        conversation.messages = conversation.messages[-(MAX_HISTORY_TURNS * 2):]
        conversation.last_active = datetime.utcnow()
        conversation.save()

        done_payload = {
            "type": "done",
            "session_id": session_id,
            "farm_id": conversation.farm_id,
            "pond_id": conversation.pond_id,
            "cycle_id": conversation.cycle_id,
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    @staticmethod
    def get_today_summary(user_id: str, farm_id: str) -> tuple:
        """Return the daily farm summary: alerts, pond status grid, and due/overdue tasks."""
        from teramina.farm.models.farm_model import Farm
        from teramina.pond.models.pond_model import Pond
        from teramina.cycle.models.cycle_model import Cycle
        from teramina.cycle_data.models.cycle_data_model import CycleData
        from teramina.helpers.constant_value import Constant

        farm = Farm.objects(id=farm_id).first()
        farm_name = farm.name if farm else farm_id

        # Alerts
        raw_alerts = FarmAlert.objects(
            user_id=user_id, farm_id=farm_id, is_read=False
        ).order_by("-created_at").limit(20)
        alerts_payload = [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "cycle_id": a.cycle_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in raw_alerts
        ]

        # Pond status grid
        ponds = Pond.objects(farm_id=farm_id, is_active=True)
        pond_status = []
        for pond in ponds:
            entry = {
                "pond_id": str(pond.id),
                "pond_name": pond.name,
                "active_cycle_id": pond.active_cycle_id or "",
                "current_doc": None,
                "do_avg": None,
                "temp_avg": None,
                "nh3": None,
                "abw_g": None,
                "do_status": "unknown",
                "nh3_status": "unknown",
            }
            if pond.active_cycle_id:
                cd = CycleData.objects(cycle_id=pond.active_cycle_id).first()
                if cd and cd.result_data:
                    rows = sorted(
                        [r for r in cd.result_data if r.get("doc")],
                        key=lambda x: x["doc"],
                    )
                    entry["current_doc"] = rows[-1]["doc"] if rows else None

                    recent = rows[-3:]
                    do_vals = [r.get("do_avg") for r in recent if r.get("do_avg")]
                    temp_vals = [r.get("temp_avg") for r in recent if r.get("temp_avg")]
                    nh3_vals = [r.get("nh3") for r in recent if r.get("nh3")]

                    if do_vals:
                        avg_do = round(sum(do_vals) / len(do_vals), 2)
                        entry["do_avg"] = avg_do
                        if avg_do < Constant.DO_SUITABLE_MIN:
                            entry["do_status"] = "critical"
                        elif avg_do < Constant.DO_OPTIMAL_MIN:
                            entry["do_status"] = "warning"
                        else:
                            entry["do_status"] = "ok"

                    if temp_vals:
                        entry["temp_avg"] = round(sum(temp_vals) / len(temp_vals), 1)

                    if nh3_vals:
                        avg_nh3 = round(sum(nh3_vals) / len(nh3_vals), 3)
                        entry["nh3"] = avg_nh3
                        if avg_nh3 > Constant.NH3_SUITABLE_MAX * 0.8:
                            entry["nh3_status"] = "critical"
                        elif avg_nh3 > Constant.NH3_OPTIMAL_MAX:
                            entry["nh3_status"] = "warning"
                        else:
                            entry["nh3_status"] = "ok"

                    abw_rows = [(r["doc"], r["abw"]) for r in rows if r.get("abw")]
                    if abw_rows:
                        entry["abw_g"] = abw_rows[-1][1]

            pond_status.append(entry)

        # ── Tasks due today or overdue ────────────────────────────────────────
        now = datetime.utcnow()
        end_of_day = now.replace(hour=23, minute=59, second=59)
        raw_tasks = WorkflowTask.objects(
            user_id=user_id, farm_id=farm_id, is_completed=False, due_at__lte=end_of_day,
        ).order_by("due_at").limit(20)
        tasks_payload = [
            {
                "id": str(t.id),
                "task_type": t.task_type,
                "title": t.title,
                "description": t.description,
                "pond_id": t.pond_id,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "is_overdue": bool(t.due_at and t.due_at < now),
            }
            for t in raw_tasks
        ]

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "farm_name": farm_name,
                "farm_id": farm_id,
                "as_of": now.isoformat(),
                "alerts": alerts_payload,
                "ponds": pond_status,
                "tasks": tasks_payload,
            },
        )

    @staticmethod
    def get_pond_timeline(user_id: str, cycle_id: str, limit: int = 50) -> tuple:
        """Return chronological event timeline for a cycle."""
        from .agent_tools import get_cycle_timeline
        result = get_cycle_timeline(cycle_id=cycle_id, limit=limit)
        if result.get("error"):
            return 400, DataErrorSchema(code=400, message=result["error"])
        return 200, DataSuccessSchema(code=200, message="OK", payload=result)

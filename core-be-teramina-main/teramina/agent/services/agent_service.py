# pylint: disable=broad-except, too-many-locals

import json
import logging
import os
import uuid
from datetime import datetime

import anthropic

from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from ..models.agent_model import AgentConversation, FarmAlert
from .agent_tools import TOOL_DEFINITIONS, TOOL_REGISTRY

logger = logging.getLogger("teramina")

MAX_HISTORY_TURNS = 20
SYSTEM_PROMPT = """You are Teramina's farm management assistant for shrimp aquaculture operations.
You help farmers understand their data, identify risks, and make better decisions.

Guidelines:
- Be specific and data-driven. Always cite actual numbers from the data.
- Lead with the most important insight first.
- When recommending action, say what to do, why, and what impact to expect.
- Respond in Indonesian if the user writes in Indonesian, otherwise in English.
- Keep responses concise — farmers read on mobile.
- If you don't have data for something, say so clearly. Do not make up numbers.
- When you see water quality issues (low DO, high NH3), flag them as urgent."""


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key)


def _build_system_with_context(farm_id: str, cycle_id: str) -> str:
    context_lines = [SYSTEM_PROMPT]
    if farm_id:
        context_lines.append(f"\nCurrent context — Farm ID: {farm_id}")
    if cycle_id:
        context_lines.append(f"Current context — Cycle ID: {cycle_id}")
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
             farm_id: str, cycle_id: str) -> tuple:
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
                cycle_id=cycle_id or "",
                messages=[],
            ).save()

        # Update context if provided
        if farm_id:
            conversation.farm_id = farm_id
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
            conversation.farm_id, conversation.cycle_id
        )

        # Agentic loop: allow up to 5 tool-call rounds
        final_text = ""
        current_messages = claude_messages.copy()
        for _ in range(5):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
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
        alert.delete()
        return 200, DataSuccessSchema(code=200, message="Alert dismissed", payload={})

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

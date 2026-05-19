# pylint: disable=broad-except

import logging
import os
from datetime import datetime

logger = logging.getLogger("teramina")


def transcribe_audio(audio_file) -> str:
    """Transcribe audio bytes using OpenAI Whisper. Returns empty string on failure."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="id",
        )
        return transcript.text or ""
    except Exception as exc:
        logger.error("whisper transcription failed: %s", exc)
        return ""


def save_note(
    user_id: str,
    content: str,
    farm_id: str = "",
    pond_id: str = "",
    cycle_id: str = "",
    source: str = "voice",
    audio_url: str = "",
    tags: list | None = None,
) -> dict:
    """Persist a FarmerNote and return its serialized form."""
    from teramina.agent.models.notes_model import FarmerNote

    note = FarmerNote(
        user_id=user_id,
        farm_id=farm_id,
        pond_id=pond_id,
        cycle_id=cycle_id,
        content=content,
        source=source,
        audio_url=audio_url,
        tags=tags or [],
    )
    note.save()
    return _serialize(note)


def save_note_to_memory(note_id: str, user_id: str) -> dict:
    """Copy a FarmerNote into AgentMemory so the agent can recall it later."""
    from teramina.agent.models.notes_model import FarmerNote
    from teramina.agent.services.agent_service import AgentService

    note = FarmerNote.objects(id=note_id, user_id=user_id).first()
    if not note:
        return {"success": False, "message": "Note not found"}
    if note.saved_to_memory:
        return {"success": False, "message": "Already saved to memory"}

    status, schema = AgentService.add_memory(
        user_id=user_id,
        farm_id=note.farm_id,
        memory_type="farmer_note",
        content=note.content,
        pond_id=note.pond_id,
        cycle_id=note.cycle_id,
        tags=note.tags,
    )
    success = status == 200
    if success:
        payload = getattr(schema, "payload", {}) or {}
        note.saved_to_memory = True
        note.memory_id = str(payload.get("id", ""))
        note.save()
    return {"success": success, "message": getattr(schema, "message", "")}


def list_notes(user_id: str, farm_id: str = "", limit: int = 20) -> list:
    qs = {"user_id": user_id}
    if farm_id:
        qs["farm_id"] = farm_id
    notes = list(
        FarmerNote_import().objects(**qs).order_by("-created_at").limit(limit)
    )
    return [_serialize(n) for n in notes]


def FarmerNote_import():
    from teramina.agent.models.notes_model import FarmerNote
    return FarmerNote


def _serialize(note) -> dict:
    return {
        "id": str(note.id),
        "content": note.content,
        "source": note.source,
        "farm_id": note.farm_id,
        "pond_id": note.pond_id,
        "cycle_id": note.cycle_id,
        "audio_url": note.audio_url,
        "tags": note.tags,
        "saved_to_memory": note.saved_to_memory,
        "memory_id": note.memory_id,
        "created_at": note.created_at.isoformat() if note.created_at else None,
    }

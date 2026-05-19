# pylint: disable=missing-function-docstring, unused-argument

import logging
from ninja import Router, File, Form
from ninja.files import UploadedFile
from typing import Optional
from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

logger = logging.getLogger("teramina")

router = Router(tags=["Farmer Notes"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema}


@router.post("/voice-note", response=response_schema, auth=AuthBearer())
def create_voice_note(
    request,
    audio: UploadedFile = File(...),
    farm_id: str = Form(""),
    pond_id: str = Form(""),
    cycle_id: str = Form(""),
    tags: str = Form(""),
):
    """Accept an audio file, transcribe via Whisper, save as FarmerNote."""
    from teramina.agent.services.voice_service import transcribe_audio, save_note

    user = get_signed_in_user(request)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    transcript = transcribe_audio(audio)
    if not transcript:
        return 400, {"success": False, "message": "Transcription failed or audio was empty"}

    note = save_note(
        user_id=str(user.id),
        content=transcript,
        farm_id=farm_id,
        pond_id=pond_id,
        cycle_id=cycle_id,
        source="voice",
        tags=tag_list,
    )
    return 200, {"success": True, "data": note}


@router.post("/text-note", response=response_schema, auth=AuthBearer())
def create_text_note(
    request,
    content: str = Form(...),
    farm_id: str = Form(""),
    pond_id: str = Form(""),
    cycle_id: str = Form(""),
    tags: str = Form(""),
):
    """Save a typed farmer note directly."""
    from teramina.agent.services.voice_service import save_note

    user = get_signed_in_user(request)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    if not content.strip():
        return 400, {"success": False, "message": "Content cannot be empty"}

    note = save_note(
        user_id=str(user.id),
        content=content.strip(),
        farm_id=farm_id,
        pond_id=pond_id,
        cycle_id=cycle_id,
        source="text",
        tags=tag_list,
    )
    return 200, {"success": True, "data": note}


@router.get("/notes", response=response_schema, auth=AuthBearer())
def get_notes(request, farm_id: str = "", limit: int = 20):
    from teramina.agent.services.voice_service import list_notes

    user = get_signed_in_user(request)
    notes = list_notes(str(user.id), farm_id=farm_id, limit=min(limit, 100))
    return 200, {"success": True, "data": notes}


@router.post("/notes/{note_id}/save-to-memory", response=response_schema, auth=AuthBearer())
def save_note_to_memory(request, note_id: str):
    from teramina.agent.services.voice_service import save_note_to_memory as _save

    user = get_signed_in_user(request)
    result = _save(note_id, str(user.id))
    status = 200 if result.get("success") else 400
    return status, result

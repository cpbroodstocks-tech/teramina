"""Tests for farmer notes creation, listing, and memory linking."""

from unittest.mock import MagicMock, patch

import pytest

USER_ID = "user-notes-001"
FARM_ID = "farm-notes-001"
POND_ID = "pond-notes-001"
CYCLE_ID = "cycle-notes-001"


def _clear():
    from teramina.agent.models.notes_model import FarmerNote
    FarmerNote.objects.delete()


@pytest.mark.django_db
class TestSaveNote:
    def setup_method(self):
        _clear()

    def teardown_method(self):
        _clear()

    def test_save_text_note(self):
        from teramina.agent.services.voice_service import save_note
        note = save_note(
            user_id=USER_ID,
            content="Warna air berubah menjadi coklat",
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            source="text",
        )
        assert note["content"] == "Warna air berubah menjadi coklat"
        assert note["source"] == "text"
        assert note["farm_id"] == FARM_ID
        assert not note["saved_to_memory"]
        assert note["id"]

    def test_save_voice_note(self):
        from teramina.agent.services.voice_service import save_note
        note = save_note(
            user_id=USER_ID,
            content="Udang terlihat aktif dan nafsu makan bagus",
            farm_id=FARM_ID,
            source="voice",
            tags=["observation", "feeding"],
        )
        assert note["source"] == "voice"
        assert "observation" in note["tags"]
        assert "feeding" in note["tags"]

    def test_save_note_empty_tags_default(self):
        from teramina.agent.services.voice_service import save_note
        note = save_note(user_id=USER_ID, content="Short note")
        assert note["tags"] == []


@pytest.mark.django_db
class TestListNotes:
    def setup_method(self):
        _clear()

    def teardown_method(self):
        _clear()

    def test_list_returns_user_notes_only(self):
        from teramina.agent.services.voice_service import save_note, list_notes
        save_note(user_id=USER_ID, content="Note 1", farm_id=FARM_ID)
        save_note(user_id=USER_ID, content="Note 2", farm_id=FARM_ID)
        save_note(user_id="other-user", content="Other note", farm_id=FARM_ID)

        notes = list_notes(USER_ID, farm_id=FARM_ID)
        assert len(notes) == 2
        assert all(n["farm_id"] == FARM_ID for n in notes)

    def test_list_ordered_by_newest_first(self):
        from datetime import datetime, timedelta
        from teramina.agent.services.voice_service import list_notes
        from teramina.agent.models.notes_model import FarmerNote
        now = datetime(2025, 1, 1, 12, 0, 0)
        FarmerNote(user_id=USER_ID, content="First", farm_id=FARM_ID, created_at=now).save()
        FarmerNote(user_id=USER_ID, content="Second", farm_id=FARM_ID, created_at=now + timedelta(seconds=1)).save()

        notes = list_notes(USER_ID, farm_id=FARM_ID)
        assert notes[0]["content"] == "Second"

    def test_list_respects_limit(self):
        from teramina.agent.services.voice_service import save_note, list_notes
        for i in range(5):
            save_note(user_id=USER_ID, content=f"Note {i}", farm_id=FARM_ID)

        notes = list_notes(USER_ID, farm_id=FARM_ID, limit=3)
        assert len(notes) == 3

    def test_list_no_farm_filter(self):
        from teramina.agent.services.voice_service import save_note, list_notes
        save_note(user_id=USER_ID, content="Farm A note", farm_id="farm-a")
        save_note(user_id=USER_ID, content="Farm B note", farm_id="farm-b")

        notes = list_notes(USER_ID)
        assert len(notes) == 2


@pytest.mark.django_db
class TestTranscription:
    def test_transcribe_audio_calls_whisper(self):
        mock_file = MagicMock()
        mock_transcript = MagicMock()
        mock_transcript.text = "Pakan sisa banyak hari ini"

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = mock_transcript

        with patch("os.getenv", return_value="fake-key"), \
             patch("openai.OpenAI", return_value=mock_client):
            from teramina.agent.services import voice_service
            result = voice_service.transcribe_audio(mock_file)

        assert result == "Pakan sisa banyak hari ini"
        mock_client.audio.transcriptions.create.assert_called_once()

    def test_transcribe_audio_returns_empty_on_exception(self):
        mock_file = MagicMock()
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API error")

        with patch("os.getenv", return_value="fake-key"), \
             patch("openai.OpenAI", return_value=mock_client):
            from teramina.agent.services import voice_service
            result = voice_service.transcribe_audio(mock_file)

        assert result == ""


@pytest.mark.django_db
class TestSaveNoteToMemory:
    def setup_method(self):
        _clear()
        from teramina.agent.models.agent_model import AgentMemory
        AgentMemory.objects.delete()

    def teardown_method(self):
        _clear()
        from teramina.agent.models.agent_model import AgentMemory
        AgentMemory.objects.delete()

    def test_save_to_memory_links_note(self):
        from teramina.agent.services.voice_service import save_note, save_note_to_memory
        note = save_note(user_id=USER_ID, content="Tambak bau amonia", farm_id=FARM_ID)
        note_id = note["id"]

        result = save_note_to_memory(note_id, USER_ID)
        assert result.get("success")

        from teramina.agent.models.notes_model import FarmerNote
        updated = FarmerNote.objects(id=note_id).first()
        assert updated.saved_to_memory is True

    def test_save_to_memory_wrong_user_fails(self):
        from teramina.agent.services.voice_service import save_note, save_note_to_memory
        note = save_note(user_id=USER_ID, content="Some note", farm_id=FARM_ID)

        result = save_note_to_memory(note["id"], "wrong-user")
        assert not result.get("success")

    def test_save_to_memory_idempotent(self):
        from teramina.agent.services.voice_service import save_note, save_note_to_memory
        note = save_note(user_id=USER_ID, content="Already saved", farm_id=FARM_ID)
        save_note_to_memory(note["id"], USER_ID)

        result = save_note_to_memory(note["id"], USER_ID)
        assert not result.get("success")
        assert "already" in result.get("message", "").lower()

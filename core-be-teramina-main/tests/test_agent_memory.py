"""Tests for Teramina agent memory services and tools."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from teramina.agent.models.agent_model import (
    AgentConversation,
    AgentMemory,
    FarmAlert,
    MemoryEntity,
    MemoryObservation,
    MemoryRelation,
)
from teramina.agent.controllers import agent_controller
from teramina.agent.schemas.agent_schema import MemoryCreateSchema
from teramina.agent.services.agent_service import AgentService, SYSTEM_PROMPT, _build_memory_context
from teramina.agent.services.agent_tools import save_farm_memory, search_farm_memory


USER_ID = "user-memory-001"
FARM_ID = "farm-memory-001"
POND_ID = "pond-memory-001"
CYCLE_ID = "cycle-memory-001"


def _clear_memory_collections():
    AgentConversation.objects.delete()
    AgentMemory.objects.delete()
    FarmAlert.objects.delete()
    MemoryEntity.objects.delete()
    MemoryObservation.objects.delete()
    MemoryRelation.objects.delete()


def _mock_chat_client(captured_requests):
    client = MagicMock()

    def create_response(**kwargs):
        captured_requests.append(kwargs)
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(text="Recommendation: Monitor pond.\nReason: Test.\nSource: test\nConfidence: low")],
        )

    client.messages.create.side_effect = create_response
    return client


class TestAgentMemoryService:

    def setup_method(self):
        _clear_memory_collections()

    def test_add_memory_creates_flat_memory_and_graph_observation(self):
        status, response = AgentService.add_memory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            memory_type="preference",
            content="Farmer prefers harvesting Pond A around size 40.",
            tags=["harvest", "preference"],
            confidence=0.95,
        )

        assert status == 200
        assert response.payload["id"]

        memory = AgentMemory.objects(user_id=USER_ID).first()
        assert memory.memory_type == "preference"
        assert memory.is_verified is True
        assert memory.confidence == 0.95

        observation = MemoryObservation.objects(user_id=USER_ID).first()
        assert observation.observation_type == "preference"
        assert observation.source_type == "farmer"
        assert observation.source_ref == f"agent_memory:{response.payload['id']}"
        assert observation.is_verified is True

    def test_get_memories_filters_by_pond(self):
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "note",
            "Pond A had low DO after rain.",
            pond_id=POND_ID,
            tags=["do"],
        )
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "note",
            "Pond B has no issues.",
            pond_id="other-pond",
        )

        status, response = AgentService.get_memories(USER_ID, FARM_ID, POND_ID)

        assert status == 200
        assert response.payload["count"] == 1
        assert response.payload["memories"][0]["content"] == "Pond A had low DO after rain."

    def test_delete_memory_removes_only_requested_user_memory(self):
        _, response = AgentService.add_memory(USER_ID, FARM_ID, "note", "Delete me")
        memory_id = response.payload["id"]

        status, delete_response = AgentService.delete_memory(memory_id, USER_ID)

        assert status == 200
        assert delete_response.message == "Memory deleted"
        assert AgentMemory.objects(id=memory_id).first() is None

    def test_delete_memory_removes_linked_graph_observation(self):
        _, response = AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Remove this graph observation too.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
        )
        memory_id = response.payload["id"]

        status, _ = AgentService.delete_memory(memory_id, USER_ID)

        assert status == 200
        assert AgentMemory.objects(id=memory_id).first() is None
        assert MemoryObservation.objects(source_ref=f"agent_memory:{memory_id}").count() == 0
        assert MemoryObservation.objects(content="Remove this graph observation too.").count() == 0

    def test_delete_memory_removes_legacy_matching_graph_observation_without_source_ref(self):
        _, response = AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "note",
            "Legacy observation cleanup.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
        )
        memory_id = response.payload["id"]
        observation = MemoryObservation.objects(source_ref=f"agent_memory:{memory_id}").first()
        observation.source_ref = ""
        observation.save()

        status, _ = AgentService.delete_memory(memory_id, USER_ID)

        assert status == 200
        assert MemoryObservation.objects(content="Legacy observation cleanup.").count() == 0

    def test_build_memory_context_prioritizes_matching_verified_memory(self):
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Pond A had low DO after heavy rain.",
            pond_id=POND_ID,
            confidence=0.9,
        )
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "note",
            "Feed brand changed last cycle.",
            pond_id=POND_ID,
            confidence=0.6,
        )

        context = _build_memory_context(USER_ID, FARM_ID, POND_ID, "Why was DO low?")

        assert "Relevant durable memories" in context
        assert "Pond A had low DO after heavy rain." in context
        assert "conf=0.9" in context

    def test_get_memory_graph_returns_entities_relations_and_observations(self):
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Pond A recovered after added aeration.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            tags=["aeration"],
        )

        status, response = AgentService.get_memory_graph(USER_ID, FARM_ID, POND_ID)

        assert status == 200
        payload = response.payload
        assert len(payload["entities"]) >= 2
        assert len(payload["relations"]) >= 1
        assert len(payload["observations"]) == 1
        assert payload["observations"][0]["content"] == "Pond A recovered after added aeration."


class TestAgentChatContext:

    def setup_method(self):
        _clear_memory_collections()

    def test_chat_without_context_does_not_inject_context_ids(self):
        captured_requests = []

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            status, response = AgentService.chat(USER_ID, "What should I check today?", "", "", "", "")

        assert status == 200
        assert response.payload["farm_id"] == ""
        system = captured_requests[0]["system"]
        assert "Current context" not in system
        assert "Relevant durable memories" not in system

    def test_chat_with_farm_only_injects_farm_context(self):
        captured_requests = []

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            status, response = AgentService.chat(USER_ID, "Summarize farm risk.", "", FARM_ID, "", "")

        assert status == 200
        assert response.payload["farm_id"] == FARM_ID
        system = captured_requests[0]["system"]
        assert f"Current context — Farm ID: {FARM_ID}" in system
        assert "Current context — Pond ID:" not in system
        assert "Current context — Cycle ID:" not in system

    def test_chat_with_full_context_injects_memory_and_persists_context(self):
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Pond A DO dropped after overnight rain.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            confidence=0.9,
        )
        captured_requests = []

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            status, response = AgentService.chat(
                USER_ID, "Why did DO drop?", "session-full-context", FARM_ID, POND_ID, CYCLE_ID
            )

        assert status == 200
        assert response.payload["farm_id"] == FARM_ID
        assert response.payload["pond_id"] == POND_ID
        assert response.payload["cycle_id"] == CYCLE_ID
        system = captured_requests[0]["system"]
        assert f"Current context — Farm ID: {FARM_ID}" in system
        assert f"Current context — Pond ID: {POND_ID}" in system
        assert f"Current context — Cycle ID: {CYCLE_ID}" in system
        assert "Pond A DO dropped after overnight rain." in system

        conversation = AgentConversation.objects(session_id="session-full-context").first()
        assert conversation.farm_id == FARM_ID
        assert conversation.pond_id == POND_ID
        assert conversation.cycle_id == CYCLE_ID

    def test_chat_updates_existing_session_context(self):
        captured_requests = []

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            AgentService.chat(USER_ID, "Start farm session.", "session-context-update", FARM_ID, "", "")
            status, response = AgentService.chat(
                USER_ID, "Now focus on pond.", "session-context-update", "", POND_ID, CYCLE_ID
            )

        assert status == 200
        assert response.payload["farm_id"] == FARM_ID
        assert response.payload["pond_id"] == POND_ID
        assert response.payload["cycle_id"] == CYCLE_ID

        conversation = AgentConversation.objects(session_id="session-context-update").first()
        assert conversation.farm_id == FARM_ID
        assert conversation.pond_id == POND_ID
        assert conversation.cycle_id == CYCLE_ID

    def test_system_prompt_blocks_speculative_memory_writes(self):
        assert "Do not save speculative information" in SYSTEM_PROMPT
        assert "only save facts the farmer has confirmed or data you have directly observed" in SYSTEM_PROMPT


class TestAgentAlerts:

    def setup_method(self):
        _clear_memory_collections()

    def _create_alert(self):
        return FarmAlert(
            user_id=USER_ID,
            farm_id=FARM_ID,
            cycle_id=CYCLE_ID,
            alert_type="water_quality",
            severity="critical",
            message="DO is below safe range.",
            data={"do": 2.9},
            expires_at=datetime.utcnow() + timedelta(days=1),
        ).save()

    def test_dismiss_alert_removes_only_requested_user_alert(self):
        alert = self._create_alert()

        status, response = AgentService.dismiss_alert(str(alert.id), USER_ID)

        assert status == 200
        assert response.message == "Alert dismissed"
        assert FarmAlert.objects(id=alert.id).first() is None

    def test_resolve_alert_marks_read_and_creates_advice_memory_for_action_note(self):
        alert = self._create_alert()

        status, response = AgentService.resolve_alert(str(alert.id), USER_ID, "Added aeration for two hours.")

        assert status == 200
        assert response.message == "Alert resolved"

        refreshed = FarmAlert.objects(id=alert.id).first()
        assert refreshed.is_read is True
        assert refreshed.resolved_at is not None
        assert refreshed.resolution_note == "Added aeration for two hours."
        assert refreshed.outcome_memory_id

        memory = AgentMemory.objects(id=refreshed.outcome_memory_id).first()
        assert memory.memory_type == "advice"
        assert memory.is_verified is True
        assert "Added aeration for two hours." in memory.content

    def test_resolve_alert_without_action_note_does_not_create_memory(self):
        alert = self._create_alert()

        status, _ = AgentService.resolve_alert(str(alert.id), USER_ID, "")

        assert status == 200
        refreshed = FarmAlert.objects(id=alert.id).first()
        assert refreshed.is_read is True
        assert refreshed.outcome_memory_id == ""
        assert AgentMemory.objects(user_id=USER_ID).count() == 0


class TestAgentMemoryTools:

    def setup_method(self):
        _clear_memory_collections()

    def test_save_farm_memory_clamps_confidence_and_searches_by_tag(self):
        farm = MagicMock()
        farm.user_id = USER_ID
        with patch("teramina.agent.services.agent_tools.Farm") as MockFarm:
            MockFarm.objects.return_value.first.return_value = farm
            result = save_farm_memory(
                FARM_ID,
                "event",
                "DO improved after extra aeration.",
                pond_id=POND_ID,
                tags=["do", "aeration"],
                confidence=1.5,
            )

        assert result["saved"] is True
        memory = AgentMemory.objects(farm_id=FARM_ID).first()
        assert memory.confidence == 1.0

        search = search_farm_memory(FARM_ID, query="aeration", pond_id=POND_ID)
        assert search["count"] >= 1
        assert any("extra aeration" in memory["content"] for memory in search["memories"])


class TestAgentMemoryControllers:

    def setup_method(self):
        _clear_memory_collections()

    def _request(self):
        return MagicMock()

    def _signed_in_user(self):
        return SimpleNamespace(id=USER_ID)

    def test_add_memory_controller_uses_signed_in_user_and_returns_id(self):
        payload = MemoryCreateSchema(
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            memory_type="note",
            content="Controller saved memory.",
            tags=["controller"],
            confidence=0.8,
        )

        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, response = agent_controller.add_memory(self._request(), payload)

        assert status == 200
        assert response.payload["id"]
        memory = AgentMemory.objects(id=response.payload["id"]).first()
        assert memory.user_id == USER_ID
        assert memory.farm_id == FARM_ID

    def test_get_memories_controller_filters_by_context(self):
        AgentService.add_memory(USER_ID, FARM_ID, "note", "Visible memory.", pond_id=POND_ID)
        AgentService.add_memory(USER_ID, FARM_ID, "note", "Hidden memory.", pond_id="other-pond")

        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, response = agent_controller.get_memories(self._request(), FARM_ID, POND_ID)

        assert status == 200
        assert response.payload["count"] == 1
        assert response.payload["memories"][0]["content"] == "Visible memory."

    def test_get_memory_graph_controller_returns_graph_payload(self):
        AgentService.add_memory(USER_ID, FARM_ID, "event", "Controller graph memory.", pond_id=POND_ID)

        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, response = agent_controller.get_memory_graph(self._request(), FARM_ID, POND_ID)

        assert status == 200
        assert response.payload["entities"]
        assert response.payload["relations"]
        assert response.payload["observations"][0]["content"] == "Controller graph memory."

    def test_delete_memory_controller_removes_memory_and_graph_observation(self):
        _, create_response = AgentService.add_memory(USER_ID, FARM_ID, "note", "Controller delete memory.")
        memory_id = create_response.payload["id"]

        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, response = agent_controller.delete_memory(self._request(), memory_id)

        assert status == 200
        assert response.message == "Memory deleted"
        assert AgentMemory.objects(id=memory_id).first() is None
        assert MemoryObservation.objects(source_ref=f"agent_memory:{memory_id}").count() == 0

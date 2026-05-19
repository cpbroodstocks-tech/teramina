"""Tests for Teramina agent memory services and tools."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from teramina.agent.models.agent_model import (
    AgentConversation,
    AgentMemory,
    FarmAlert,
    MemoryEmbedding,
    MemoryEntity,
    MemoryObservation,
    MemoryRelation,
)
from teramina.agent.controllers import agent_controller
from teramina.agent.schemas.agent_schema import MemoryCreateSchema
from teramina.agent.services.agent_service import AgentService, SYSTEM_PROMPT, _build_memory_context
from teramina.agent.services.agent_tools import (
    TOOL_REGISTRY,
    get_pond_history,
    save_farm_memory,
    search_farm_memory,
    search_memory,
)
from teramina.agent.services.memory_retrieval import index_agent_memory, semantic_search_memories
from teramina.helpers.management.commands.backfill_agent_memory_graph import backfill_agent_memory_graph


USER_ID = "user-memory-001"
FARM_ID = "farm-memory-001"
POND_ID = "pond-memory-001"
CYCLE_ID = "cycle-memory-001"


def _clear_memory_collections():
    AgentConversation.objects.delete()
    AgentMemory.objects.delete()
    FarmAlert.objects.delete()
    MemoryEmbedding.objects.delete()
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

    def test_update_memory_corrects_flat_graph_and_embedding_records(self):
        _, response = AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "note",
            "Pond A has low DO every morning.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            tags=["old"],
            confidence=0.5,
        )
        memory_id = response.payload["id"]

        status, update_response = AgentService.update_memory(
            memory_id,
            USER_ID,
            memory_type="event",
            content="Pond A had low DO after heavy rain.",
            tags=["do", "rain"],
            confidence=1.2,
        )

        assert status == 200
        assert update_response.message == "Memory updated"
        memory = AgentMemory.objects(id=memory_id).first()
        assert memory.memory_type == "event"
        assert memory.content == "Pond A had low DO after heavy rain."
        assert memory.tags == ["do", "rain"]
        assert memory.confidence == 1.0
        assert memory.is_verified is True

        observation = MemoryObservation.objects(source_ref=f"agent_memory:{memory_id}").first()
        assert observation.observation_type == "event_summary"
        assert observation.content == "Pond A had low DO after heavy rain."
        assert observation.confidence == 1.0
        assert observation.is_verified is True

        embedding = MemoryEmbedding.objects(source_ref=f"agent_memory:{memory_id}").first()
        assert embedding.content == "Pond A had low DO after heavy rain."

    def test_update_memory_rejects_empty_content(self):
        _, response = AgentService.add_memory(USER_ID, FARM_ID, "note", "Keep me")

        status, update_response = AgentService.update_memory(response.payload["id"], USER_ID, content="   ")

        assert status == 400
        assert update_response.message == "Memory content is required"

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
        page_context = {
            "route": "/dashboard/pond-timeline/cycle-memory-001",
            "page_type": "pond_timeline",
            "farm_id": FARM_ID,
            "pond_id": POND_ID,
            "cycle_id": CYCLE_ID,
            "filters": {"status": "active"},
        }

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            status, response = AgentService.chat(
                USER_ID, "Why did DO drop?", "session-full-context", FARM_ID, POND_ID, CYCLE_ID, page_context
            )

        assert status == 200
        assert response.payload["farm_id"] == FARM_ID
        assert response.payload["pond_id"] == POND_ID
        assert response.payload["cycle_id"] == CYCLE_ID
        assert response.payload["page_context"] == page_context
        system = captured_requests[0]["system"]
        assert f"Current context — Farm ID: {FARM_ID}" in system
        assert f"Current context — Pond ID: {POND_ID}" in system
        assert f"Current context — Cycle ID: {CYCLE_ID}" in system
        assert "Current page context — type=pond_timeline" in system
        assert "Pond A DO dropped after overnight rain." in system

        conversation = AgentConversation.objects(session_id="session-full-context").first()
        assert conversation.farm_id == FARM_ID
        assert conversation.pond_id == POND_ID
        assert conversation.cycle_id == CYCLE_ID
        assert conversation.page_context == page_context

    def test_chat_updates_existing_session_context(self):
        captured_requests = []

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            AgentService.chat(USER_ID, "Start farm session.", "session-context-update", FARM_ID, "", "")
            status, response = AgentService.chat(
                USER_ID,
                "Now focus on pond.",
                "session-context-update",
                "",
                POND_ID,
                CYCLE_ID,
                {"route": "/cycle/cycle-memory-001", "page_type": "cycle", "cycle_id": CYCLE_ID, "filters": {}},
            )

        assert status == 200
        assert response.payload["farm_id"] == FARM_ID
        assert response.payload["pond_id"] == POND_ID
        assert response.payload["cycle_id"] == CYCLE_ID

        conversation = AgentConversation.objects(session_id="session-context-update").first()
        assert conversation.farm_id == FARM_ID
        assert conversation.pond_id == POND_ID
        assert conversation.cycle_id == CYCLE_ID
        assert conversation.page_context["page_type"] == "cycle"

    def test_system_prompt_blocks_speculative_memory_writes(self):
        assert "Do not save speculative information" in SYSTEM_PROMPT
        assert "only save facts the farmer has confirmed or data you have directly observed" in SYSTEM_PROMPT
        assert "include memory ref/pond/cycle when using durable memory" in SYSTEM_PROMPT

    def test_chat_injects_retrieved_low_do_memory_with_source_ref_and_context_ids(self):
        _, create_response = AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Pond A had low DO after overnight rain and recovered after aeration.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            confidence=0.9,
        )
        captured_requests = []

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            status, response = AgentService.chat(
                USER_ID, "Why did low DO happen before?", "session-low-do", FARM_ID, POND_ID, CYCLE_ID
            )

        assert status == 200
        assert response.payload["farm_id"] == FARM_ID
        system = captured_requests[0]["system"]
        assert "Pond A had low DO after overnight rain" in system
        assert f"pond={POND_ID}" in system
        assert f"cycle={CYCLE_ID}" in system
        assert f"ref=agent_memory:{create_response.payload['id']}" in system

    def test_chat_retrieves_harvest_history_memory_for_related_question(self):
        _, create_response = AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "advice",
            "Last cycle harvest worked best after partial harvest at DOC 95.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            confidence=0.85,
        )
        captured_requests = []

        with patch("teramina.agent.services.agent_service._get_client", return_value=_mock_chat_client(captured_requests)):
            status, response = AgentService.chat(
                USER_ID, "What happened last time near harvest?", "session-harvest-history", FARM_ID, POND_ID, CYCLE_ID
            )

        assert status == 200
        assert response.payload["cycle_id"] == CYCLE_ID
        system = captured_requests[0]["system"]
        assert "Last cycle harvest worked best" in system
        assert f"ref=agent_memory:{create_response.payload['id']}" in system


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

    def test_save_farm_memory_requires_confirmation(self):
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
            )

        assert result["saved"] is False
        assert AgentMemory.objects(farm_id=FARM_ID).count() == 0

    def test_save_farm_memory_clamps_confidence_and_searches_by_tag_after_confirmation(self):
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
                confirmed=True,
            )

        assert result["saved"] is True
        memory = AgentMemory.objects(farm_id=FARM_ID).first()
        assert memory.confidence == 1.0
        assert memory.source == "user_input"
        assert memory.is_verified is True
        assert MemoryEmbedding.objects(source_ref=f"agent_memory:{memory.id}").count() == 1

        search = search_farm_memory(FARM_ID, query="aeration", pond_id=POND_ID)
        assert search["count"] >= 1
        assert search["retrieval"] in {"semantic", "lexical_fallback"}
        assert any("extra aeration" in memory["content"] for memory in search["memories"])

    def test_search_memory_alias_is_registered_and_scoped(self):
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Pond A low DO improved after extra aeration.",
            pond_id=POND_ID,
            tags=["do", "aeration"],
        )
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Other pond feed tray was clean.",
            pond_id="other-pond",
        )

        result = search_memory(FARM_ID, query="aeration", pond_id=POND_ID)

        assert TOOL_REGISTRY["search_memory"] is search_memory
        assert result["count"] >= 1
        assert all(memory["pond_id"] == POND_ID for memory in result["memories"])

    def test_get_pond_history_groups_recurring_actions_harvest_and_notes(self):
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Pond A has recurring low DO after rain.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            tags=["water_quality"],
        )
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "advice",
            "Extra aeration worked before.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
        )
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "event",
            "Harvest outcome was better after partial harvest.",
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
        )
        AgentService.add_memory(
            USER_ID,
            FARM_ID,
            "note",
            "Farmer prefers morning checks.",
            pond_id=POND_ID,
        )

        history = get_pond_history(FARM_ID, POND_ID)

        assert TOOL_REGISTRY["get_pond_history"] is get_pond_history
        assert history["count"] >= 4
        assert any("recurring low DO" in item["content"] for item in history["recurring_issues"])
        assert any("Extra aeration worked" in item["content"] for item in history["what_worked_before"])
        assert any("Harvest outcome" in item["content"] for item in history["past_harvest_outcomes"])
        assert any("morning checks" in item["content"] for item in history["notes"])


class TestAgentMemoryRetrieval:

    def setup_method(self):
        _clear_memory_collections()

    def test_semantic_search_falls_back_to_lexical_without_embeddings(self):
        AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            memory_type="event",
            content="Low DO improved after extra aeration.",
            tags=["aeration"],
            confidence=0.9,
            is_verified=True,
        ).save()
        AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id="other-pond",
            memory_type="event",
            content="Feed tray was clean.",
            confidence=0.9,
            is_verified=True,
        ).save()

        result = semantic_search_memories(FARM_ID, query="aeration", pond_id=POND_ID, user_id=USER_ID)

        assert result["retrieval"] == "lexical_fallback"
        assert result["count"] == 1
        assert result["memories"][0]["content"] == "Low DO improved after extra aeration."

    def test_semantic_search_uses_indexed_embeddings_and_respects_pond_scope(self):
        target = AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            memory_type="event",
            content="Pond A recovered after emergency aeration overnight.",
            tags=["do", "aeration"],
            confidence=0.9,
            is_verified=True,
        ).save()
        other = AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id="other-pond",
            memory_type="event",
            content="Other pond recovered after emergency aeration.",
            tags=["do", "aeration"],
            confidence=0.9,
            is_verified=True,
        ).save()
        index_agent_memory(target)
        index_agent_memory(other)

        result = semantic_search_memories(FARM_ID, query="emergency aeration", pond_id=POND_ID, user_id=USER_ID)

        assert result["retrieval"] == "semantic"
        assert result["count"] == 1
        assert result["memories"][0]["source_ref"] == f"agent_memory:{target.id}"

    def test_semantic_search_logs_retrieval_metrics(self):
        memory = AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            memory_type="event",
            content="Aeration recovered low DO.",
            confidence=0.8,
            is_verified=True,
        ).save()
        index_agent_memory(memory)

        with patch("teramina.agent.services.memory_retrieval.logger.info") as mock_log:
            semantic_search_memories(FARM_ID, query="aeration", pond_id=POND_ID, user_id=USER_ID)

        mock_log.assert_called_once()
        assert mock_log.call_args.args[1] == FARM_ID
        assert mock_log.call_args.args[2] == POND_ID
        assert mock_log.call_args.args[3] == "semantic"

    def test_get_memories_filters_low_confidence_review_queue(self):
        AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            memory_type="note",
            content="Needs review.",
            confidence=0.4,
        ).save()
        AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            memory_type="note",
            content="High confidence.",
            confidence=0.9,
        ).save()

        status, response = AgentService.get_memories(USER_ID, FARM_ID, max_confidence=0.5)

        assert status == 200
        assert response.payload["count"] == 1
        assert response.payload["memories"][0]["content"] == "Needs review."

    def test_add_memory_indexes_flat_memory_and_observation(self):
        _, response = AgentService.add_memory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            memory_type="note",
            content="Farmer noted cloudy water after rain.",
        )
        memory_id = response.payload["id"]
        observation = MemoryObservation.objects(source_ref=f"agent_memory:{memory_id}").first()

        assert MemoryEmbedding.objects(source_ref=f"agent_memory:{memory_id}").count() == 1
        assert MemoryEmbedding.objects(source_ref=f"memory_observation:{observation.id}").count() == 1

    def test_delete_memory_removes_memory_embeddings(self):
        _, response = AgentService.add_memory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            memory_type="note",
            content="Delete indexed memory.",
        )
        memory_id = response.payload["id"]
        observation = MemoryObservation.objects(source_ref=f"agent_memory:{memory_id}").first()

        AgentService.delete_memory(memory_id, USER_ID)

        assert MemoryEmbedding.objects(source_ref=f"agent_memory:{memory_id}").count() == 0
        assert MemoryEmbedding.objects(source_ref=f"memory_observation:{observation.id}").count() == 0


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

    def test_get_memories_controller_filters_by_max_confidence(self):
        AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            memory_type="note",
            content="Controller low confidence memory.",
            confidence=0.3,
        ).save()
        AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            memory_type="note",
            content="Controller high confidence memory.",
            confidence=0.9,
        ).save()

        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, response = agent_controller.get_memories(
                self._request(), farm_id=FARM_ID, max_confidence=0.5
            )

        assert status == 200
        assert response.payload["count"] == 1
        assert response.payload["memories"][0]["content"] == "Controller low confidence memory."

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

    def test_verify_memory_sets_verified_and_updates_linked_observations(self):
        _, create_response = AgentService.add_memory(
            USER_ID, FARM_ID, "advice", "Aeration helps after rain.", pond_id=POND_ID,
            confidence=0.5,
        )
        memory_id = create_response.payload["id"]
        # force unverified so we can assert the transition
        AgentMemory.objects(id=memory_id).update(is_verified=False)
        MemoryObservation.objects(
            user_id=USER_ID, source_ref=f"agent_memory:{memory_id}"
        ).update(is_verified=False)

        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, response = agent_controller.verify_memory(self._request(), memory_id)

        assert status == 200
        assert response.payload["id"] == memory_id
        assert AgentMemory.objects(id=memory_id).first().is_verified is True
        for obs in MemoryObservation.objects(user_id=USER_ID, source_ref=f"agent_memory:{memory_id}"):
            assert obs.is_verified is True

    def test_verify_memory_returns_400_for_unknown_id(self):
        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, response = agent_controller.verify_memory(self._request(), "nonexistent-id")

        assert status == 400
        assert "not found" in response.message.lower()

    def test_verify_memory_cannot_access_other_users_memory(self):
        other_mem = AgentMemory(
            user_id="other-user",
            farm_id=FARM_ID,
            memory_type="note",
            content="Other user memory.",
            confidence=0.4,
            is_verified=False,
        ).save()

        with patch.object(agent_controller, "get_signed_in_user", return_value=self._signed_in_user()):
            status, _ = agent_controller.verify_memory(self._request(), str(other_mem.id))

        assert status == 400
        assert AgentMemory.objects(id=other_mem.id).first().is_verified is False


class TestAgentMemoryBackfill:

    def setup_method(self):
        _clear_memory_collections()

    def test_backfill_dry_run_reports_without_writing(self):
        memory = AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            memory_type="event",
            content="Legacy memory needs a graph observation.",
            source="user_input",
            confidence=1.4,
            is_verified=True,
        ).save()

        stats = backfill_agent_memory_graph(apply=False, user_id=USER_ID)

        assert stats["memories_scanned"] == 1
        assert stats["observations_created"] == 1
        assert stats["memories_normalized"] == 1
        assert AgentMemory.objects(id=memory.id).first().confidence == 1.4
        assert MemoryObservation.objects(source_ref=f"agent_memory:{memory.id}").count() == 0

    def test_backfill_apply_creates_observation_and_clamps_memory_confidence(self):
        memory = AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            memory_type="event",
            content="Backfilled event observation.",
            source="user_input",
            confidence=1.4,
            is_verified=True,
        ).save()

        stats = backfill_agent_memory_graph(apply=True, user_id=USER_ID)

        assert stats["memories_scanned"] == 1
        assert stats["observations_created"] == 1
        assert stats["memories_normalized"] == 1

        refreshed = AgentMemory.objects(id=memory.id).first()
        assert refreshed.confidence == 1.0

        observation = MemoryObservation.objects(source_ref=f"agent_memory:{memory.id}").first()
        assert observation is not None
        assert observation.content == "Backfilled event observation."
        assert observation.source_type == "farmer"
        assert observation.is_verified is True
        assert observation.confidence == 1.0

    def test_backfill_apply_links_newest_legacy_observation_and_reports_duplicates(self):
        memory = AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            memory_type="note",
            content="Legacy duplicate observation.",
            source="agent_inference",
            confidence=0.6,
            is_verified=False,
        ).save()
        older = MemoryObservation(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            entity_id="legacy-entity",
            observation_type="note",
            content="Legacy duplicate observation.",
            confidence=0.6,
            created_at=datetime.utcnow() - timedelta(days=1),
        ).save()
        newer = MemoryObservation(
            user_id=USER_ID,
            farm_id=FARM_ID,
            pond_id=POND_ID,
            cycle_id=CYCLE_ID,
            entity_id="legacy-entity",
            observation_type="note",
            content="Legacy duplicate observation.",
            confidence=0.6,
            created_at=datetime.utcnow(),
        ).save()

        stats = backfill_agent_memory_graph(apply=True, user_id=USER_ID)

        assert stats["observations_linked"] == 1
        assert stats["observations_created"] == 0
        assert stats["duplicate_legacy_observations"] == 1

        assert MemoryObservation.objects(id=newer.id).first().source_ref == f"agent_memory:{memory.id}"
        assert MemoryObservation.objects(id=older.id).first().source_ref == ""

    def test_backfill_filters_by_farm(self):
        AgentMemory(
            user_id=USER_ID,
            farm_id=FARM_ID,
            memory_type="note",
            content="Included farm memory.",
        ).save()
        other = AgentMemory(
            user_id=USER_ID,
            farm_id="other-farm",
            memory_type="note",
            content="Excluded farm memory.",
        ).save()

        stats = backfill_agent_memory_graph(apply=True, farm_id=FARM_ID)

        assert stats["memories_scanned"] == 1
        assert MemoryObservation.objects(content="Included farm memory.").count() == 1
        assert MemoryObservation.objects(source_ref=f"agent_memory:{other.id}").count() == 0

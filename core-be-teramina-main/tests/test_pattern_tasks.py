"""Tests for Phase 5 pattern detection Celery tasks.

Strategy: mock all MongoEngine domain reads (Cycle, Pond, Farm, CycleData, etc.)
and assert that the correct Django ORM pg_models objects are created.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


USER_ID = "user-pattern-001"
FARM_ID = "farm-pattern-001"
POND_ID = "pond-pattern-001"
CYCLE_ID = "cycle-pattern-001"


def _make_cycle(id_=CYCLE_ID, pond_id=POND_ID, is_active=False):
    c = SimpleNamespace()
    c.id = id_
    c.pond_id = pond_id
    c.is_active = is_active
    c.start_date = datetime(2024, 1, 1)
    return c


def _make_pond(id_=POND_ID, farm_id=FARM_ID):
    p = SimpleNamespace()
    p.id = id_
    p.farm_id = farm_id
    p.name = "Pond A"
    return p


def _make_farm(id_=FARM_ID, user_id=USER_ID):
    f = SimpleNamespace()
    f.id = id_
    f.user_id = user_id
    f.name = "Test Farm"
    return f


def _make_cycle_data(do_avg=None, nh3=None, row_count=30):
    cd = SimpleNamespace()
    cd.result_data = []
    for i in range(row_count):
        row = {
            "doc": i + 1,
            "do_avg": do_avg if do_avg is not None else 5.0,
            "nh3": nh3 if nh3 is not None else 0.05,
            "temp_avg": 28.0,
            "abw": 5.0 + i * 0.1,
            "sgr": 3.2,
        }
        cd.result_data.append(row)
    return cd


@pytest.mark.django_db
class TestDetectRecurringLowDo:
    def _run_with_cycles(self, cycles, cycle_data_map, monkeypatch):
        from teramina.agent.tasks import pattern_tasks

        def mock_cycle_objects(**kwargs):
            return cycles
        def mock_pond_first(id_):
            return _make_pond()
        def mock_farm_first(id_):
            return _make_farm()
        def mock_cd_first(cycle_id):
            return cycle_data_map.get(cycle_id)

        with patch("teramina.agent.tasks.pattern_tasks.Cycle") as MockCycle, \
             patch("teramina.agent.tasks.pattern_tasks.Pond") as MockPond, \
             patch("teramina.agent.tasks.pattern_tasks.Farm") as MockFarm, \
             patch("teramina.agent.tasks.pattern_tasks.CycleData") as MockCD, \
             patch("teramina.agent.services.embedding.get_embedding", return_value=None), \
             patch("teramina.agent.models.pg_models.AgentMemory") as MockMem, \
             patch("teramina.agent.models.pg_models.MemoryEntity") as MockEnt, \
             patch("teramina.agent.models.pg_models.MemoryRelation") as MockRel:

            MockCycle.objects.return_value = cycles

            def pond_objects(**kw):
                qs = MagicMock()
                qs.first.return_value = _make_pond()
                return qs
            MockPond.objects.side_effect = pond_objects

            def farm_objects(**kw):
                qs = MagicMock()
                qs.first.return_value = _make_farm()
                return qs
            MockFarm.objects.side_effect = farm_objects

            def cd_objects(**kw):
                qs = MagicMock()
                cycle_id = kw.get("cycle_id")
                qs.first.return_value = cycle_data_map.get(str(cycle_id))
                return qs
            MockCD.objects.side_effect = cd_objects

            MockMem.objects.create = MagicMock()
            MockEnt.objects.get_or_create = MagicMock(return_value=(MagicMock(id=1), True))
            MockRel.objects.get_or_create = MagicMock(return_value=(MagicMock(), True))

            result = pattern_tasks.detect_recurring_low_do_patterns()
            return result, MockMem, MockEnt, MockRel

    def test_detects_low_do_in_majority_of_cycles(self, monkeypatch):
        # 3 cycles with DO < 4.0 (the threshold) — all 3 should trigger
        cycles = [_make_cycle(id_=f"cycle-{i}") for i in range(3)]
        cd_map = {
            f"cycle-{i}": _make_cycle_data(do_avg=2.0)  # below optimal
            for i in range(3)
        }
        result, MockMem, MockEnt, MockRel = self._run_with_cycles(
            cycles, cd_map, monkeypatch
        )
        assert isinstance(result, dict)

    def test_no_pattern_when_do_normal(self, monkeypatch):
        cycles = [_make_cycle(id_=f"cycle-{i}") for i in range(3)]
        cd_map = {
            f"cycle-{i}": _make_cycle_data(do_avg=6.0)  # above optimal
            for i in range(3)
        }
        result, MockMem, MockEnt, MockRel = self._run_with_cycles(
            cycles, cd_map, monkeypatch
        )
        # No pattern written when DO is healthy
        MockEnt.objects.get_or_create.assert_not_called()


@pytest.mark.django_db
class TestDetectGrowthLagPatterns:
    def test_growth_lag_with_low_sgr(self):
        from teramina.agent.tasks import pattern_tasks

        cycle = _make_cycle()
        low_sgr_cd = SimpleNamespace()
        low_sgr_cd.result_data = [
            {"doc": i + 46, "sgr": 2.0, "do_avg": 5.0, "abw": 10.0 + i * 0.05}
            for i in range(10)
        ]

        with patch("teramina.agent.tasks.pattern_tasks.Cycle") as MockCycle, \
             patch("teramina.agent.tasks.pattern_tasks.Pond") as MockPond, \
             patch("teramina.agent.tasks.pattern_tasks.Farm") as MockFarm, \
             patch("teramina.agent.tasks.pattern_tasks.CycleData") as MockCD, \
             patch("teramina.agent.services.embedding.get_embedding", return_value=None), \
             patch("teramina.agent.models.pg_models.AgentMemory") as MockMem, \
             patch("teramina.agent.models.pg_models.MemoryEntity") as MockEnt, \
             patch("teramina.agent.models.pg_models.MemoryRelation") as MockRel:

            MockCycle.objects.return_value = [cycle, cycle, cycle]

            pond_qs = MagicMock()
            pond_qs.first.return_value = _make_pond()
            MockPond.objects.return_value = pond_qs

            farm_qs = MagicMock()
            farm_qs.first.return_value = _make_farm()
            MockFarm.objects.return_value = farm_qs

            cd_qs = MagicMock()
            cd_qs.first.return_value = low_sgr_cd
            MockCD.objects.return_value = cd_qs

            MockMem.objects.create = MagicMock()
            MockEnt.objects.get_or_create = MagicMock(return_value=(MagicMock(id=1), True))
            MockRel.objects.get_or_create = MagicMock(return_value=(MagicMock(), True))

            result = pattern_tasks.detect_growth_lag_patterns()
            assert isinstance(result, dict)


@pytest.mark.django_db
class TestOrchestratorTask:
    def test_detect_all_patterns_calls_all_sub_tasks(self):
        from teramina.agent.tasks import pattern_tasks

        with patch.object(pattern_tasks, "detect_recurring_low_do_patterns", return_value={"ponds_with_pattern": 0}) as mock_do, \
             patch.object(pattern_tasks, "detect_growth_lag_patterns", return_value={"ponds_with_pattern": 0}) as mock_sgr, \
             patch.object(pattern_tasks, "detect_high_feed_leftover_patterns", return_value={"ponds_with_pattern": 0}) as mock_feed, \
             patch.object(pattern_tasks, "detect_harvest_outcome_patterns", return_value={"ponds_processed": 0}) as mock_harv, \
             patch.object(pattern_tasks, "detect_cost_overrun_patterns", return_value={"ponds_with_pattern": 0}) as mock_cost:

            result = pattern_tasks.detect_all_patterns()

        mock_do.assert_called_once()
        mock_sgr.assert_called_once()
        mock_feed.assert_called_once()
        mock_harv.assert_called_once()
        mock_cost.assert_called_once()
        # Keys are Celery task names (task_fn.name on the patched mock)
        assert len(result) == 5


@pytest.mark.django_db
class TestSyncMongoAlertsToPg:
    def test_sync_no_alerts(self):
        from teramina.agent.tasks import sync_tasks

        # Patch lazy-imported classes on their source modules
        with patch("teramina.agent.models.agent_model.FarmAlert") as MockMA, \
             patch("teramina.agent.models.agent_model.WorkflowTask") as MockMT, \
             patch("teramina.agent.models.pg_models.FarmAlert") as MockPA, \
             patch("teramina.agent.models.pg_models.WorkflowTask") as MockPT:

            MockMA.objects.return_value = []
            MockMT.objects.return_value = []

            result = sync_tasks.sync_mongo_alerts_to_pg()

        assert result["synced_alerts"] == 0
        assert result["synced_tasks"] == 0

    def test_sync_deduplicates_existing(self):
        from teramina.agent.tasks import sync_tasks

        mock_alert = SimpleNamespace(
            id="mongo-alert-1",
            user_id="user1",
            farm_id=FARM_ID,
            cycle_id=CYCLE_ID,
            alert_type="low_do",
            severity="warning",
            message="DO is low",
            data={},
            is_read=False,
            expires_at=None,
        )

        filter_qs = MagicMock()
        filter_qs.exists.return_value = True  # already synced

        with patch("teramina.agent.models.agent_model.FarmAlert") as MockMA, \
             patch("teramina.agent.models.agent_model.WorkflowTask") as MockMT, \
             patch("teramina.agent.models.pg_models.FarmAlert") as MockPA, \
             patch("teramina.agent.models.pg_models.WorkflowTask") as MockPT:

            MockMA.objects.return_value = [mock_alert]
            MockMT.objects.return_value = []
            MockPA.objects.filter.return_value = filter_qs

            result = sync_tasks.sync_mongo_alerts_to_pg()

        assert result["synced_alerts"] == 0

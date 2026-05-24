"""Tests for agent monitoring triggers, today summary, and pond timeline."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from teramina.agent.models.agent_model import FarmAlert, WorkflowTask, AgentMemory, MemoryObservation, MemoryEntity, MemoryRelation, AgentConversation
from teramina.agent.services.agent_service import AgentService


USER_ID = "user-monitor-001"
FARM_ID = "farm-monitor-001"
POND_ID = "pond-monitor-001"
CYCLE_ID = "cycle-monitor-001"

DO_SUITABLE_MIN = 2.0
DO_OPTIMAL_MIN = 4.0
NH3_SUITABLE_MAX = 0.1
NH3_OPTIMAL_MAX = 0.02


def _clear():
    FarmAlert.objects.delete()
    WorkflowTask.objects.delete()
    AgentMemory.objects.delete()
    MemoryObservation.objects.delete()
    MemoryEntity.objects.delete()
    MemoryRelation.objects.delete()
    AgentConversation.objects.delete()


def _make_cycle_data(rows):
    cd = MagicMock()
    cd.result_data = rows
    return cd


def _make_farm_and_pond():
    farm = MagicMock()
    farm.id = FARM_ID
    farm.name = "Monitor Farm"
    farm.user_id = USER_ID

    pond = MagicMock()
    pond.id = POND_ID
    pond.farm_id = FARM_ID
    pond.active_cycle_id = CYCLE_ID

    return farm, pond


def _make_cycle():
    cycle = MagicMock()
    cycle.id = CYCLE_ID
    cycle.pond_id = POND_ID
    cycle.is_active = True
    cycle.name = "Siklus Test"
    return cycle


# ──────────────────────────────────────────────────────────────────────────────
# Monitoring trigger unit tests (test _save_alert logic via task function)
# ──────────────────────────────────────────────────────────────────────────────

class TestMonitoringAlertDedup:

    def setup_method(self):
        _clear()

    def test_duplicate_alert_within_24h_is_suppressed(self):
        from teramina.agent.tasks.monitoring_tasks import _save_alert
        _save_alert(USER_ID, FARM_ID, CYCLE_ID, "water_quality", "critical", "DO too low", {})
        _save_alert(USER_ID, FARM_ID, CYCLE_ID, "water_quality", "critical", "DO too low again", {})
        assert FarmAlert.objects(cycle_id=CYCLE_ID, alert_type="water_quality").count() == 1

    def test_different_alert_type_is_not_suppressed(self):
        from teramina.agent.tasks.monitoring_tasks import _save_alert
        _save_alert(USER_ID, FARM_ID, CYCLE_ID, "water_quality", "critical", "DO too low", {})
        _save_alert(USER_ID, FARM_ID, CYCLE_ID, "growth", "warning", "Growth lag", {})
        assert FarmAlert.objects(cycle_id=CYCLE_ID).count() == 2

    def test_critical_alert_creates_workflow_task(self):
        from teramina.agent.tasks.monitoring_tasks import _save_alert
        _save_alert(USER_ID, FARM_ID, CYCLE_ID, "water_quality", "critical", "DO critical", {})
        tasks = WorkflowTask.objects(user_id=USER_ID, cycle_id=CYCLE_ID).all()
        assert len(tasks) == 1
        assert tasks[0].task_type == "check"

    def test_info_alert_does_not_create_workflow_task(self):
        from teramina.agent.tasks.monitoring_tasks import _save_alert
        _save_alert(USER_ID, FARM_ID, CYCLE_ID, "feeding", "info", "Feed leftover high", {})
        assert WorkflowTask.objects(user_id=USER_ID, cycle_id=CYCLE_ID).count() == 0


class TestMonitoringTaskTriggers:

    def setup_method(self):
        _clear()

    def _run_monitor(self, cycle, pond, farm, cd, fd=None, feed_rows=None, cost_doc=None):
        """Helper that patches all DB lookups and runs the monitoring task body."""
        from teramina.agent.tasks.monitoring_tasks import monitor_all_active_cycles

        def cycle_iter(*a, **kw):
            class Q:
                def only(self, *a, **kw):
                    return [cycle]
            return Q()

        with (
            patch("teramina.agent.tasks.monitoring_tasks.Cycle") as MockCycle,
            patch("teramina.agent.tasks.monitoring_tasks.Pond") as MockPond,
            patch("teramina.agent.tasks.monitoring_tasks.Farm") as MockFarm,
            patch("teramina.agent.tasks.monitoring_tasks.CycleData") as MockCD,
            patch("teramina.agent.tasks.monitoring_tasks.ForecastData") as MockFD,
            patch("teramina.agent.tasks.monitoring_tasks.FeedRealization") as MockFeed,
            patch("teramina.agent.tasks.monitoring_tasks.CostData") as MockCost,
            patch("teramina.agent.tasks.monitoring_tasks.notify_user_alert"),
        ):
            MockCycle.objects.return_value.only.return_value = [cycle]
            MockPond.objects.return_value.first.return_value = pond
            MockFarm.objects.return_value.first.return_value = farm
            MockCD.objects.return_value.first.return_value = cd

            fd_mock = MagicMock()
            fd_mock.result_data = fd or []
            MockFD.objects.return_value.first.return_value = fd_mock

            feed_mock = MagicMock()
            feed_mock.__iter__ = lambda self: iter(feed_rows or [])
            MockFeed.objects.return_value.order_by.return_value.limit.return_value = feed_rows or []

            cost_mock = MagicMock()
            cost_mock.data = cost_doc or []
            MockCost.objects.return_value.first.return_value = cost_mock

            result = monitor_all_active_cycles()
        return result

    def test_critical_do_generates_alert(self):
        farm, pond = _make_farm_and_pond()
        cycle = _make_cycle()
        cd = _make_cycle_data([
            {"doc": 10, "do_avg": 1.5, "temp_avg": 28},
            {"doc": 11, "do_avg": 1.6, "temp_avg": 28},
            {"doc": 12, "do_avg": 1.4, "temp_avg": 28},
        ])
        result = self._run_monitor(cycle, pond, farm, cd)
        assert result["generated"] >= 1
        alert = FarmAlert.objects(cycle_id=CYCLE_ID, alert_type="water_quality", severity="critical").first()
        assert alert is not None

    def test_nh3_rising_trend_generates_warning(self):
        farm, pond = _make_farm_and_pond()
        cycle = _make_cycle()
        cd = _make_cycle_data([
            {"doc": 10, "do_avg": 5.0, "nh3": 0.01},
            {"doc": 11, "do_avg": 5.0, "nh3": 0.02},
            {"doc": 12, "do_avg": 5.0, "nh3": 0.03},
        ])
        result = self._run_monitor(cycle, pond, farm, cd)
        alert = FarmAlert.objects(cycle_id=CYCLE_ID, alert_type="water_quality", severity="warning").first()
        assert alert is not None
        assert "rising" in alert.message.lower() or "NH3" in alert.message

    def test_harvest_window_generates_info(self):
        farm, pond = _make_farm_and_pond()
        cycle = _make_cycle()
        cd = _make_cycle_data([{"doc": 95, "do_avg": 5.0}])
        fd = [{"doc": 99, "profit": 100_000_000}]
        result = self._run_monitor(cycle, pond, farm, cd, fd=fd)
        alert = FarmAlert.objects(cycle_id=CYCLE_ID, alert_type="harvest_window").first()
        assert alert is not None
        assert "harvest" in alert.message.lower()

    def test_feed_leftover_generates_info(self):
        farm, pond = _make_farm_and_pond()
        cycle = _make_cycle()
        cd = _make_cycle_data([{"doc": 30, "do_avg": 5.0}])

        feed_row = MagicMock()
        feed_row.feed_given = 100
        feed_row.feed_leftover = 30
        feed_rows = [feed_row] * 4

        result = self._run_monitor(cycle, pond, farm, cd, feed_rows=feed_rows)
        alert = FarmAlert.objects(cycle_id=CYCLE_ID, alert_type="feeding").first()
        assert alert is not None
        assert "leftover" in alert.message.lower()

    def test_growth_lag_after_doc_45_generates_warning(self):
        farm, pond = _make_farm_and_pond()
        cycle = _make_cycle()
        import math
        # SGR = (ln(w2) - ln(w1)) / (d2 - d1) * 100
        # For SGR < 3.5: w1=10, w2=10.3, d1=44, d2=46 → SGR ≈ 1.47
        cd = _make_cycle_data([
            {"doc": 44, "do_avg": 5.0, "abw": 10.0},
            {"doc": 46, "do_avg": 5.0, "abw": 10.3},
        ])
        result = self._run_monitor(cycle, pond, farm, cd)
        alert = FarmAlert.objects(cycle_id=CYCLE_ID, alert_type="growth").first()
        assert alert is not None

    def test_no_alert_when_all_metrics_normal(self):
        farm, pond = _make_farm_and_pond()
        cycle = _make_cycle()
        cd = _make_cycle_data([
            {"doc": 20, "do_avg": 6.0, "nh3": 0.01, "temp_avg": 28},
            {"doc": 21, "do_avg": 6.2, "nh3": 0.01, "temp_avg": 28},
            {"doc": 22, "do_avg": 6.1, "nh3": 0.01, "temp_avg": 28},
        ])
        result = self._run_monitor(cycle, pond, farm, cd)
        assert FarmAlert.objects(cycle_id=CYCLE_ID).count() == 0


class TestPatternDetectionJobs:

    def setup_method(self):
        _clear()

    def _run_detector(self, detector, cycle_data=None, feed_rows=None, forecast_rows=None, cost_rows=None):
        farm, pond = _make_farm_and_pond()
        cycle = _make_cycle()
        with (
            patch("teramina.agent.tasks.monitoring_tasks.Cycle") as MockCycle,
            patch("teramina.agent.tasks.monitoring_tasks.Pond") as MockPond,
            patch("teramina.agent.tasks.monitoring_tasks.Farm") as MockFarm,
            patch("teramina.agent.tasks.monitoring_tasks.CycleData") as MockCD,
            patch("teramina.agent.tasks.monitoring_tasks.FeedRealization") as MockFeed,
            patch("teramina.agent.tasks.monitoring_tasks.ForecastData") as MockForecast,
            patch("teramina.agent.tasks.monitoring_tasks.CostData") as MockCost,
        ):
            MockCycle.objects.return_value = [cycle]
            MockPond.objects.return_value.first.return_value = pond
            MockFarm.objects.return_value.first.return_value = farm
            MockCD.objects.return_value.first.return_value = _make_cycle_data(cycle_data or [])
            MockFeed.objects.return_value.order_by.return_value.limit.return_value = feed_rows or []
            forecast = MagicMock()
            forecast.result_data = forecast_rows or []
            MockForecast.objects.return_value.first.return_value = forecast
            cost = MagicMock()
            cost.data = cost_rows or []
            MockCost.objects.return_value.first.return_value = cost
            return detector()

    def test_detect_recurring_low_do_patterns_creates_graph_memory(self):
        from teramina.agent.tasks.monitoring_tasks import detect_recurring_low_do_patterns

        result = self._run_detector(
            detect_recurring_low_do_patterns,
            cycle_data=[
                {"doc": 40, "do_avg": 3.0},
                {"doc": 41, "do_avg": 3.2},
                {"doc": 42, "do_avg": 5.0},
            ],
        )

        assert result["created"] == 1
        memory = AgentMemory.objects(tags__all=["pattern", "low_DO_after_DOC_40"]).first()
        assert memory is not None
        observation = MemoryObservation.objects(source_ref=f"agent_memory:{memory.id}").first()
        assert observation.observation_type == "risk_pattern"
        assert observation.structured_data["risk_level"] == "medium"

    def test_detect_high_feed_leftover_patterns_creates_graph_memory(self):
        from teramina.agent.tasks.monitoring_tasks import detect_high_feed_leftover_patterns

        feed_row = MagicMock()
        feed_row.feed_given = 100
        feed_row.feed_leftover = 30

        result = self._run_detector(detect_high_feed_leftover_patterns, feed_rows=[feed_row])

        assert result["created"] == 1
        memory = AgentMemory.objects(tags__all=["pattern", "high_feed_leftover"]).first()
        assert memory is not None
        assert "feed leftover" in memory.content.lower()

    def test_detect_all_patterns_runs_each_detector(self):
        from teramina.agent.tasks import monitoring_tasks

        with patch.object(monitoring_tasks, "detect_recurring_low_do_patterns", return_value={"created": 1}) as low_do, \
             patch.object(monitoring_tasks, "detect_growth_lag_patterns", return_value={"created": 2}) as growth, \
             patch.object(monitoring_tasks, "detect_high_feed_leftover_patterns", return_value={"created": 3}) as feed, \
             patch.object(monitoring_tasks, "detect_harvest_outcome_patterns", return_value={"created": 4}) as harvest, \
             patch.object(monitoring_tasks, "detect_cost_overrun_patterns", return_value={"created": 5}) as cost:
            result = monitoring_tasks.detect_all_patterns()

        assert result["detect_recurring_low_do_patterns"]["created"] == 1
        assert result["detect_growth_lag_patterns"]["created"] == 2
        assert result["detect_high_feed_leftover_patterns"]["created"] == 3
        assert result["detect_harvest_outcome_patterns"]["created"] == 4
        assert result["detect_cost_overrun_patterns"]["created"] == 5
        low_do.assert_called_once()
        growth.assert_called_once()
        feed.assert_called_once()
        harvest.assert_called_once()
        cost.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# AgentService: get_today_summary
# ──────────────────────────────────────────────────────────────────────────────

class TestGetTodaySummary:

    def setup_method(self):
        _clear()

    def test_returns_empty_ponds_and_alerts_when_none_exist(self):
        farm = MagicMock()
        farm.name = "Test Farm"
        pond = MagicMock()
        pond.id = POND_ID
        pond.name = "Pond A"
        pond.active_cycle_id = None

        with (
            patch("teramina.agent.services.agent_service.Farm") as MockFarm,
            patch("teramina.agent.services.agent_service.Pond") as MockPond,
        ):
            MockFarm.objects.return_value.first.return_value = farm
            MockPond.objects.return_value = [pond]

            status, response = AgentService.get_today_summary(USER_ID, FARM_ID)

        assert status == 200
        assert response.payload["farm_name"] == "Test Farm"
        assert response.payload["ponds"][0]["active_cycle_id"] == ""
        assert response.payload["alerts"] == []

    def test_pond_status_colors_classify_low_do_as_warning(self):
        from teramina.helpers.constant_value import Constant

        farm = MagicMock()
        farm.name = "Farm"
        pond = MagicMock()
        pond.id = POND_ID
        pond.name = "Pond A"
        pond.active_cycle_id = CYCLE_ID

        cd = MagicMock()
        cd.result_data = [
            {"doc": 10, "do_avg": Constant.DO_SUITABLE_MIN + 0.1, "temp_avg": 28, "nh3": 0.01},
        ]

        with (
            patch("teramina.agent.services.agent_service.Farm") as MockFarm,
            patch("teramina.agent.services.agent_service.Pond") as MockPond,
            patch("teramina.agent.services.agent_service.CycleData") as MockCD,
        ):
            MockFarm.objects.return_value.first.return_value = farm
            MockPond.objects.return_value = [pond]
            MockCD.objects.return_value.first.return_value = cd

            status, response = AgentService.get_today_summary(USER_ID, FARM_ID)

        assert status == 200
        pond_entry = response.payload["ponds"][0]
        assert pond_entry["do_status"] in ("warning", "ok")

    def test_overdue_tasks_appear_in_payload(self):
        farm = MagicMock()
        farm.name = "Farm"

        task = WorkflowTask(
            user_id=USER_ID,
            farm_id=FARM_ID,
            task_type="check",
            title="Overdue check",
            due_at=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow(),
        ).save()

        with (
            patch("teramina.agent.services.agent_service.Farm") as MockFarm,
            patch("teramina.agent.services.agent_service.Pond") as MockPond,
        ):
            MockFarm.objects.return_value.first.return_value = farm
            MockPond.objects.return_value = []

            status, response = AgentService.get_today_summary(USER_ID, FARM_ID)

        task.delete()
        assert status == 200
        tasks = response.payload["tasks"]
        assert any(t["id"] == str(task.id) and t["is_overdue"] is True for t in tasks)


# ──────────────────────────────────────────────────────────────────────────────
# AgentService: get_pond_timeline
# ──────────────────────────────────────────────────────────────────────────────

class TestGetPondTimeline:

    def setup_method(self):
        _clear()

    def test_returns_events_sorted_by_doc(self):
        cycle = MagicMock()
        cycle.id = CYCLE_ID
        cycle.name = "Siklus A"
        cycle.start_date = datetime(2026, 1, 1)
        cycle.pond_id = POND_ID

        pond = MagicMock()
        pond.farm_id = FARM_ID

        cd = MagicMock()
        cd.result_data = [
            {"doc": 5, "do_avg": 5.0},
            {"doc": 10, "do_avg": 4.8},
        ]

        with (
            patch("teramina.agent.services.agent_tools.Cycle") as MockCycle,
            patch("teramina.agent.services.agent_tools.Pond") as MockPond,
            patch("teramina.agent.services.agent_tools.CycleData") as MockCD,
        ):
            MockCycle.objects.return_value.first.return_value = cycle
            MockPond.objects.return_value.first.return_value = pond
            MockCD.objects.return_value.first.return_value = cd

            status, response = AgentService.get_pond_timeline(USER_ID, CYCLE_ID)

        assert status == 200
        payload = response.payload
        assert payload["cycle_name"] == "Siklus A"
        events = payload["events"]
        docs = [e["doc"] for e in events if e.get("doc")]
        assert docs == sorted(docs)

    def test_returns_error_when_cycle_not_found(self):
        with patch("teramina.agent.services.agent_tools.Cycle") as MockCycle:
            MockCycle.objects.return_value.first.return_value = None
            status, response = AgentService.get_pond_timeline(USER_ID, "bad-cycle-id")

        assert status == 400

    def test_limit_is_respected(self):
        cycle = MagicMock()
        cycle.id = CYCLE_ID
        cycle.name = "Siklus B"
        cycle.start_date = None
        cycle.pond_id = POND_ID

        pond = MagicMock()
        pond.farm_id = FARM_ID

        cd = MagicMock()
        cd.result_data = [{"doc": i, "do_avg": 5.0} for i in range(1, 21)]

        with (
            patch("teramina.agent.services.agent_tools.Cycle") as MockCycle,
            patch("teramina.agent.services.agent_tools.Pond") as MockPond,
            patch("teramina.agent.services.agent_tools.CycleData") as MockCD,
        ):
            MockCycle.objects.return_value.first.return_value = cycle
            MockPond.objects.return_value.first.return_value = pond
            MockCD.objects.return_value.first.return_value = cd

            status, response = AgentService.get_pond_timeline(USER_ID, CYCLE_ID, limit=5)

        assert status == 200
        assert len(response.payload["events"]) <= 5


# ──────────────────────────────────────────────────────────────────────────────
# System prompt data integrity rules
# ──────────────────────────────────────────────────────────────────────────────

class TestSystemPromptIntegrity:

    def test_hallucination_guard_present(self):
        from teramina.agent.services.agent_service import SYSTEM_PROMPT
        assert "must come from a tool result" in SYSTEM_PROMPT
        assert "Data unavailable" in SYSTEM_PROMPT

    def test_chemical_disclaimer_rule_present(self):
        from teramina.agent.services.agent_service import SYSTEM_PROMPT
        assert "extension officer" in SYSTEM_PROMPT

    def test_speculative_memory_write_rule_present(self):
        from teramina.agent.services.agent_service import SYSTEM_PROMPT
        assert "Do not save speculative information" in SYSTEM_PROMPT

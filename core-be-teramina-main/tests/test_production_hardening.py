"""Regression tests for production-hardening fixes."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from teramina.cost_data.models.cost_data_model import CostData
from teramina.agent.controllers.agent_controller import get_summary_result, request_summary
from teramina.agent.schemas.agent_schema import SummaryRequestSchema
from teramina.cycle.models.cycle_model import Data
from teramina.cycle_data.models.cycle_data_model import (
    CycleData,
    ForecastData,
    ResultData,
)
from teramina.farm.models.farm_model import Farm
from teramina.helpers.ownership import verify_cycle_owner, verify_farm_owner, verify_pond_owner
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.middleware.rate_limit import RateLimitMiddleware
from teramina.dashboard.controllers.dashboard_controller import overview
from teramina.pond.controllers.pond_controller import set_active_cycle
from teramina.pond.models.pond_model import Pond
from teramina.user.models.user_model import User
from teramina.schemas.general_schema import DataSuccessSchema
from teramina.water_quality_dashboard.controllers.variable_controller import update_variable
from teramina.water_quality_dashboard.controllers.water_quality_controller import _owns_cycles


def test_set_active_cycle_checks_pond_and_cycle_ownership():
    request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer token"})

    with (
        patch("teramina.pond.controllers.pond_controller.get_signed_in_user", return_value=SimpleNamespace(id="user-1")),
        patch("teramina.pond.controllers.pond_controller.verify_pond_owner", return_value=True) as verify_pond,
        patch("teramina.pond.controllers.pond_controller.verify_cycle_owner", return_value=True) as verify_cycle,
        patch("teramina.pond.controllers.pond_controller.PondService.set_active_cycle", return_value=(200, "ok")),
    ):
        assert set_active_cycle(request, "pond-1", "cycle-1") == (200, "ok")

    verify_pond.assert_called_once_with("pond-1", "user-1")
    verify_cycle.assert_called_once_with("cycle-1", "user-1")


def test_datetime_model_defaults_are_callables():
    fields = [
        Farm.created_at,
        Pond.created_at,
        User.created_at,
        Data.last_updated,
        FeedRealization.last_updated,
        HarvestRecommendation.last_updated,
        HarvestRecord.last_updated,
        CycleData.last_updated,
        ResultData.last_updated,
        ForecastData.last_updated,
        CostData.last_updated,
    ]

    assert all(callable(field.default) for field in fields)


def test_rate_limit_uses_atomic_route_scoped_counter():
    response = object()
    middleware = RateLimitMiddleware(MagicMock(return_value=response))
    request = SimpleNamespace(path_info="/api/user/login", META={"REMOTE_ADDR": "127.0.0.1"})

    with patch("teramina.middleware.rate_limit.cache") as cache:
        cache.incr.side_effect = ValueError
        cache.add.return_value = True

        assert middleware(request) is response

    key = cache.add.call_args.args[0]
    assert key.startswith("rl:/api/user/login:127.0.0.1:")
    cache.add.assert_called_once_with(key, 1, timeout=120)


def test_rate_limit_allows_limit_then_rejects_next_request():
    downstream = MagicMock(return_value=object())
    middleware = RateLimitMiddleware(downstream)
    request = SimpleNamespace(path_info="/api/user/login", META={"REMOTE_ADDR": "127.0.0.1"})

    with patch("teramina.middleware.rate_limit.cache") as cache:
        cache.incr.side_effect = [10, 11]
        allowed = middleware(request)
        rejected = middleware(request)

    assert allowed is downstream.return_value
    assert rejected.status_code == 429
    assert downstream.call_count == 1


def test_dashboard_rejects_farm_owned_by_another_user():
    request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer token"})

    with (
        patch("teramina.dashboard.controllers.dashboard_controller.get_signed_in_user", return_value=SimpleNamespace(id="user-1")),
        patch("teramina.dashboard.controllers.dashboard_controller.verify_farm_owner", return_value=False),
    ):
        status, response = overview(request, "another-users-farm")

    assert status == 401
    assert response.message == "Unauthorized"


def test_water_quality_requires_ownership_of_every_cycle():
    request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer token"})

    with (
        patch("teramina.water_quality_dashboard.controllers.water_quality_controller.get_signed_in_user", return_value=SimpleNamespace(id="user-1")),
        patch("teramina.water_quality_dashboard.controllers.water_quality_controller.verify_cycle_owner", side_effect=[True, False]) as verify,
    ):
        assert not _owns_cycles(request, "cycle-1,cycle-2")

    assert verify.call_count == 2


def test_only_admin_can_update_global_water_quality_variables():
    request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer token"})

    with patch(
        "teramina.water_quality_dashboard.controllers.variable_controller.get_signed_in_user",
        return_value=SimpleNamespace(id="user-1", role_user="user"),
    ):
        status, response = update_variable(request, MagicMock())

    assert status == 401
    assert response.message == "Unauthorized"


def test_malformed_resource_ids_are_not_owned():
    assert not verify_farm_owner("not-an-object-id", "user-1")
    assert not verify_pond_owner("not-an-object-id", "user-1")
    assert not verify_cycle_owner("not-an-object-id", "user-1")


def test_external_summary_task_is_bound_to_requesting_user():
    request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer token"})
    service_response = DataSuccessSchema(code=200, message="OK", payload={"task_id": "summary-1"})

    with (
        patch("teramina.agent.controllers.agent_controller.get_signed_in_user", return_value=SimpleNamespace(id="user-1")),
        patch("teramina.agent.controllers.agent_controller.AgentService.request_external_summary", return_value=(200, service_response)),
        patch("teramina.agent.controllers.agent_controller.cache") as cache,
    ):
        status, response = request_summary(request, SummaryRequestSchema(question="How is the farm?"))

    assert status == 200
    assert response is service_response
    cache.set.assert_called_once_with("agent_summary_owner:summary-1", "user-1", timeout=3600)


def test_external_summary_poll_hides_another_users_task():
    request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer token"})

    with (
        patch("teramina.agent.controllers.agent_controller.get_signed_in_user", return_value=SimpleNamespace(id="user-2")),
        patch("teramina.agent.controllers.agent_controller.cache") as cache,
        patch("teramina.agent.controllers.agent_controller.AgentService.get_external_summary_result") as service,
    ):
        cache.get.return_value = "user-1"
        status, response = get_summary_result(request, "summary-1")

    assert status == 404
    assert response.message == "Summary task not found"
    service.assert_not_called()

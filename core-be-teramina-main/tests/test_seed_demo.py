from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from teramina.advisory.models.advisory_model import AdvisoryCase, AdvisoryReport
from teramina.agent.models.agent_model import AgentMemory, FarmAlert, WorkflowTask
from teramina.content.models.content_model import ContentAccess
from teramina.cost_data.models.cost_data_model import CostData
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData, ResultData
from teramina.dashboard.services.filter_service import FilterData
from teramina.dashboard.services.historical.economic import DashboardEconomic
from teramina.dashboard.services.historical.feed import DashboardFeed
from teramina.farm.models.farm_model import Farm
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.helpers.default_data_updater import ensure_default_data_for_user, user_has_dashboard_data
from teramina.helpers.demo_artifacts import DEMO_BUNDLE_VERSION, DEMO_TAG
from teramina.helpers.management.commands.seed_demo import CURRENT_DOC, load_sample_seed_data
from teramina.pond.models.pond_model import Pond
from teramina.user.models.user_model import User
from teramina.user.services.profile_service import ProfileService
from teramina.water_quality_dashboard.models.variable_model import WQVariable
from teramina.water_quality_dashboard.services.water_quality_service import WaterQuality


SAMPLE_DATA_DIR = Path(__file__).resolve().parents[2] / "sample_data"


def _seed_template_scenarios():
    call_command("seed_demo", verbosity=0)
    farm = Farm.objects(user_id="__seed__", demo_bundle_version=DEMO_BUNDLE_VERSION).first()
    scenarios = {}
    for pond in Pond.objects(farm_id=str(farm.id)):
        cycle = Cycle.objects(id=pond.active_cycle_id, pond_id=str(pond.id), is_active=True).first()
        scenarios[pond.demo_scenario] = (pond, cycle)
    return farm, scenarios


def _end_date(cycle_id, output_format):
    value = CycleData.objects(cycle_id=cycle_id).first().result_data[-1]["date"]
    return date.fromisoformat(str(value)[:10]).strftime(output_format)


def test_sample_seed_loads_all_google_sheets_tabs():
    seed = load_sample_seed_data(SAMPLE_DATA_DIR)

    assert len(seed["daily_rows"]) == 120
    assert len(seed["result_rows"]) == 120
    assert len(seed["feed_rows"]) == 120
    assert len(seed["cost_rows"]) == 40
    assert seed["daily_rows"][0]["doc"] == 1
    assert seed["daily_rows"][-1]["doc"] == 120

    assert seed["daily_rows"][13]["abw"] == pytest.approx(0.4)
    assert seed["daily_rows"][0]["mortality_count"] == 1268

    harvest = seed["harvest_data"]
    assert harvest["partial1"]["doc"] == 95
    assert harvest["partial1"]["biomass"] == pytest.approx(2279.4)
    assert harvest["final"]["doc"] == 120
    assert harvest["final"]["biomass"] == pytest.approx(6801.0)


def test_sample_seed_builds_healthy_dashboard_rows():
    seed = load_sample_seed_data(SAMPLE_DATA_DIR)
    result_rows = seed["result_rows"]

    assert all(row["abw"] > 0 for row in result_rows)
    assert all(0 < row["sr"] <= 1 for row in result_rows)
    assert all(row["do"] > 0 for row in result_rows)
    assert all(row["ration_number"] == 1 for row in seed["feed_rows"])
    assert all("feed_ration_1" in row for row in result_rows)
    assert result_rows[-1]["sr"] == pytest.approx(0.865)
    assert result_rows[-1]["harvest_biomass_kg"] == pytest.approx(6801.0)
    assert result_rows[-1]["cum_realized_revenue"] > 0
    assert result_rows[-1]["cum_total_cost"] == pytest.approx(829_500_000)


def test_sample_seed_requires_exactly_120_daily_rows(tmp_path):
    for source in SAMPLE_DATA_DIR.glob("*.csv"):
        (tmp_path / source.name).write_bytes(source.read_bytes())

    daily_path = tmp_path / "DAILY_LOG.csv"
    lines = daily_path.read_text(encoding="utf-8").splitlines()
    daily_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    with pytest.raises(CommandError, match="Expected 120 DAILY_LOG rows"):
        load_sample_seed_data(tmp_path)


def test_seed_demo_command_persists_complete_onboarding_template():
    farm, scenarios = _seed_template_scenarios()

    assert farm.name == "Demo A/B Farm"
    assert set(scenarios) == {"healthy", "at_risk"}
    for pond, cycle in scenarios.values():
        cycle_id = str(cycle.id)
        assert pond.active_cycle_id == cycle_id
        assert cycle.start_date.date() == date.today() - timedelta(days=CURRENT_DOC - 1)
        assert len(CycleData.objects(cycle_id=cycle_id).first().result_data) == CURRENT_DOC
        assert len(ResultData.objects(cycle_id=cycle_id).first().result_data) == CURRENT_DOC
        assert len(ForecastData.objects(cycle_id=cycle_id).first().result_data) == 120
        assert FeedRealization.objects(cycle_id=cycle_id).count() == CURRENT_DOC
        assert HarvestRecord.objects(cycle_id=cycle_id).count() == 1
        assert CostData.objects(farm_id=cycle_id).first().data

    healthy_cycle = scenarios["healthy"][1]
    risk_cycle = scenarios["at_risk"][1]
    healthy = ResultData.objects(cycle_id=str(healthy_cycle.id)).first().result_data[-1]
    at_risk = ResultData.objects(cycle_id=str(risk_cycle.id)).first().result_data[-1]
    assert at_risk["do"] < healthy["do"]
    assert at_risk["nh3"] > healthy["nh3"]
    assert at_risk["abw"] < healthy["abw"]
    assert at_risk["cost_per_kg"] > healthy["cost_per_kg"]


def test_seed_demo_supports_string_date_filter_and_economics_dashboard():
    farm, scenarios = _seed_template_scenarios()
    pond, cycle = scenarios["healthy"]

    status, response = FilterData("__seed__").filter(
        str(farm.id), str(pond.id), str(cycle.id), "historical"
    )
    assert status == 200
    assert response.payload[0]["daterange"] == {
        "start_date": (date.today() - timedelta(days=CURRENT_DOC - 1)).strftime("%m/%d/%Y"),
        "end_date": date.today().strftime("%m/%d/%Y"),
    }

    status, response = DashboardEconomic(
        str(farm.id),
        str(pond.id),
        str(cycle.id),
        date.today().strftime("%m/%d/%Y"),
    ).economic()
    assert status == 200
    assert response.payload["profit_n_lost"]["data"]


def test_seed_demo_supports_csv_water_quality_parameters_and_wqi():
    farm, scenarios = _seed_template_scenarios()
    pond, cycle = scenarios["healthy"]
    cycle_id = str(cycle.id)

    assert WQVariable.objects.count() == 7
    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    cycle_data.result_data[-1].pop("turbidity")
    cycle_data.save()

    status, response = FilterData("__seed__").wq_filter(str(farm.id), str(pond.id), cycle_id)
    assert status == 200, response.message
    assert set(response.payload[0]["data"]["variables"]) == {
        "do_morning",
        "do_afternoon",
        "do_avg",
        "temp_morning",
        "temp_afternoon",
        "temp_avg",
        "ph_morning",
        "ph_afternoon",
        "salinity",
        "nh3",
        "turbidity",
        "wqi_1",
        "wqi_2",
    }

    status, response = WaterQuality().get_water_quality_data(
        cycle_id,
        (date.today() - timedelta(days=CURRENT_DOC - 1)).isoformat(),
        date.today().isoformat(),
        "wqi_1",
    )
    assert status == 200, response.message
    assert len(response.payload["data"]) == CURRENT_DOC
    assert response.payload["data"][0]["wqi_1"] is not None


@pytest.mark.parametrize("doc", [31, CURRENT_DOC])
def test_seed_demo_supports_feeding_dashboard(doc):
    farm, scenarios = _seed_template_scenarios()
    pond, cycle = scenarios["healthy"]
    query_date = (cycle.start_date.date() + timedelta(days=doc - 1)).strftime("%m/%d/%Y")

    status, response = DashboardFeed(
        str(farm.id),
        str(pond.id),
        str(cycle.id),
        query_date,
    ).feed()

    assert status == 200, response.message
    realization = next(
        item["data"]
        for item in response.payload["daily_feed_adjustment"]["data"]
        if item["title"] == "Realization"
    )
    assert len(realization["ration"]) == 4
    assert realization["ration"][0]["ration_number"] == "1"


def test_feeding_dashboard_supports_legacy_seed_rows():
    farm, scenarios = _seed_template_scenarios()
    pond, cycle = scenarios["healthy"]
    cycle_id = str(cycle.id)

    result_data = ResultData.objects(cycle_id=cycle_id).first()
    for row in result_data.result_data:
        for ration_number in range(1, 5):
            row.pop(f"feed_ration_{ration_number}", None)
    result_data.save()
    FeedRealization.objects(cycle_id=cycle_id).update(set__ration_number=0)

    status, response = DashboardFeed(
        str(farm.id),
        str(pond.id),
        cycle_id,
        _end_date(cycle_id, "%m/%d/%Y"),
    ).feed()

    assert status == 200, response.message
    realization = next(
        item["data"]
        for item in response.payload["daily_feed_adjustment"]["data"]
        if item["title"] == "Realization"
    )
    assert realization["ration"][0]["ration_number"] == "1"


def test_existing_user_without_dashboard_ready_data_gets_seed_once(monkeypatch):
    source_farm, scenarios = _seed_template_scenarios()
    source_pond, source_cycle = scenarios["healthy"]

    monkeypatch.setenv("SEEDER_FARM", str(source_farm.id))
    monkeypatch.setenv("SEEDER_POND", str(source_pond.id))
    monkeypatch.setenv("SEEDER_CYCLE", str(source_cycle.id))

    user = User(name="Existing User", email="existing-seed-test@teramina.io").save()
    invalid_farm = Farm(name="Incomplete Farm", location="Test", user_id=str(user.id)).save()
    invalid_pond = Pond(name="Incomplete Pond", farm_id=str(invalid_farm.id)).save()
    invalid_cycle = Cycle(name="Incomplete Cycle", pond_id=str(invalid_pond.id)).save()
    CycleData(cycle_id=str(invalid_cycle.id), result_data=[{"date": "2024-01-01", "doc": 1}]).save()
    ResultData(cycle_id=str(invalid_cycle.id), result_data=[{"date": "2024-01-01", "doc": 1}]).save()

    assert ensure_default_data_for_user(str(user.id)) is True
    assert user_has_dashboard_data(str(user.id)) is True
    farm_count = Farm.objects(user_id=str(user.id)).count()

    status, response = FilterData(str(user.id)).filter()
    assert status == 200
    assert str(invalid_farm.id) not in {farm["id"] for farm in response.payload}
    assert len(response.payload) == 1

    ready_farm_id = response.payload[0]["id"]
    status, response = FilterData(str(user.id)).filter(farm_id=ready_farm_id)
    assert status == 200
    assert {item["name"] for item in response.payload} == {"Scenario A - Healthy", "Scenario B - At Risk"}

    ready_pond_id = response.payload[0]["id"]
    status, response = FilterData(str(user.id)).filter(farm_id=ready_farm_id, pond_id=ready_pond_id)
    assert status == 200
    assert len(response.payload) == 1

    status, response = FilterData(str(user.id)).filter(
        str(invalid_farm.id),
        str(invalid_pond.id),
        str(invalid_cycle.id),
        "historical",
    )
    assert status == 400
    assert response.message == f"Dashboard data with cycle {invalid_cycle.id} doesn't exist"

    status, response = FilterData(str(user.id)).wq_filter(str(invalid_farm.id), str(invalid_pond.id))
    assert status == 200
    assert response.payload == []

    status, response = FilterData(str(user.id)).wq_filter(
        str(invalid_farm.id),
        str(invalid_pond.id),
        str(invalid_cycle.id),
    )
    assert status == 400
    assert response.message == f"Dashboard data with cycle {invalid_cycle.id} doesn't exist"

    assert ensure_default_data_for_user(str(user.id)) is False
    assert Farm.objects(user_id=str(user.id)).count() == farm_count


def test_existing_matching_demo_cycle_is_repaired_in_place(monkeypatch):
    source_farm, scenarios = _seed_template_scenarios()
    source_pond, source_cycle = scenarios["healthy"]

    monkeypatch.setenv("SEEDER_FARM", str(source_farm.id))
    monkeypatch.setenv("SEEDER_POND", str(source_pond.id))
    monkeypatch.setenv("SEEDER_CYCLE", str(source_cycle.id))

    user = User(name="Old Demo User", email="old-demo-test@teramina.io").save()
    farm = Farm(name=source_farm.name, location=source_farm.location, user_id=str(user.id)).save()
    pond = Pond(name=source_pond.name, farm_id=str(farm.id)).save()
    cycle = Cycle(name=source_cycle.name, pond_id=str(pond.id)).save()
    CycleData(cycle_id=str(cycle.id), result_data=[{"date": "2024-01-01", "doc": 1}]).save()
    ResultData(cycle_id=str(cycle.id), result_data=[{"date": "2024-01-01", "doc": 1}]).save()

    assert ensure_default_data_for_user(str(user.id)) is True
    assert Farm.objects(user_id=str(user.id)).count() == 1
    assert Pond.objects(farm_id=str(farm.id)).count() == 2
    assert Cycle.objects(pond_id=str(pond.id)).count() == 0
    assert {
        item.demo_scenario
        for item in Pond.objects(farm_id=str(farm.id))
    } == {"healthy", "at_risk"}
    assert user_has_dashboard_data(str(user.id)) is True


def test_user_demo_bundle_seeds_linked_modules_and_passes_validator(monkeypatch):
    call_command("seed_commercial_layer", verbosity=0)
    source_farm, scenarios = _seed_template_scenarios()
    source_pond, source_cycle = scenarios["healthy"]
    monkeypatch.setenv("SEEDER_FARM", str(source_farm.id))
    monkeypatch.setenv("SEEDER_POND", str(source_pond.id))
    monkeypatch.setenv("SEEDER_CYCLE", str(source_cycle.id))

    user = User(name="Bundle User", email="bundle-test@teramina.io").save()
    assert ensure_default_data_for_user(str(user.id)) is True

    user_id = str(user.id)
    assert FarmAlert.objects(user_id=user_id, data__demo_bundle_version=DEMO_BUNDLE_VERSION).count() == 1
    assert WorkflowTask.objects(user_id=user_id, title__startswith="[Demo]").count() == 2
    assert AgentMemory.objects(user_id=user_id, tags=DEMO_TAG).count() == 2
    assert ContentAccess.objects(user_id=user_id).count() >= 2
    assert AdvisoryCase.objects(user_id=user_id, intake_data__demo_bundle_version=DEMO_BUNDLE_VERSION).count() == 1
    assert AdvisoryReport.objects(user_id=user_id, status="delivered").count() == 1

    call_command("validate_demo_bundle", email=user.email, include_template=True, verbosity=0)


def test_user_provisioning_resolves_latest_template_when_environment_id_is_stale(monkeypatch):
    source_farm, _ = _seed_template_scenarios()
    monkeypatch.setenv("SEEDER_FARM", "stale-template-id")
    monkeypatch.delenv("SEEDER_POND", raising=False)
    monkeypatch.delenv("SEEDER_CYCLE", raising=False)

    user = User(name="Stale Env User", email="stale-env-test@teramina.io").save()

    assert ensure_default_data_for_user(str(user.id)) is True
    assert Farm.objects(user_id=str(user.id), demo_bundle_version=DEMO_BUNDLE_VERSION).count() == 1
    assert Farm.objects(id=source_farm.id).count() == 1


def test_staging_reset_is_guarded_and_preserves_template(monkeypatch):
    source_farm, _ = _seed_template_scenarios()
    monkeypatch.setenv("SEEDER_FARM", str(source_farm.id))
    user = User(name="Reset User", email="reset-test@teramina.io").save()
    assert ensure_default_data_for_user(str(user.id)) is True

    with pytest.raises(CommandError, match="only runs with --environment staging"):
        call_command("reset_staging_demo", environment="production", confirm="RESET-STAGING", verbosity=0)

    call_command("reset_staging_demo", environment="staging", confirm="RESET-STAGING", verbosity=0)

    assert User.objects(id=user.id).count() == 0
    assert Farm.objects(user_id=str(user.id)).count() == 0
    assert Farm.objects(id=source_farm.id, user_id="__seed__").count() == 1


def test_user_data_status_retries_default_seed_provisioning():
    user = User(name="Status User", email="status-seed-test@teramina.io").save()

    with (
        patch("teramina.user.services.profile_service.ensure_default_data_for_user") as ensure_default,
        patch("teramina.user.services.profile_service.sync_user_data_status", return_value=True),
    ):
        status, response = ProfileService().is_there_data_status(str(user.id))

    assert status == 200
    assert response.payload["is_there_data"] is True
    ensure_default.assert_called_once_with(str(user.id))

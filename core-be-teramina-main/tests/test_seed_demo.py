from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

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
from teramina.helpers.management.commands.seed_demo import load_sample_seed_data
from teramina.pond.models.pond_model import Pond
from teramina.user.models.user_model import User
from teramina.user.services.profile_service import ProfileService


SAMPLE_DATA_DIR = Path(__file__).resolve().parents[2] / "sample_data"


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
    call_command("seed_demo", verbosity=0)

    farm = Farm.objects(user_id="__seed__").order_by("-created_at").first()
    pond = Pond.objects(farm_id=str(farm.id)).first()
    cycle = Cycle.objects(pond_id=str(pond.id)).first()
    cycle_id = str(cycle.id)

    assert len(CycleData.objects(cycle_id=cycle_id).first().result_data) == 120
    assert len(ResultData.objects(cycle_id=cycle_id).first().result_data) == 120
    assert len(ForecastData.objects(cycle_id=cycle_id).first().result_data) == 120
    assert FeedRealization.objects(cycle_id=cycle_id).count() == 120
    assert HarvestRecord.objects(cycle_id=cycle_id).count() == 1
    assert len(CostData.objects(farm_id=cycle_id).first().data) == 40


def test_seed_demo_supports_string_date_filter_and_economics_dashboard():
    call_command("seed_demo", verbosity=0)

    farm = Farm.objects(user_id="__seed__").order_by("-created_at").first()
    pond = Pond.objects(farm_id=str(farm.id)).first()
    cycle = Cycle.objects(pond_id=str(pond.id)).first()

    status, response = FilterData("__seed__").filter(
        str(farm.id), str(pond.id), str(cycle.id), "historical"
    )
    assert status == 200
    assert response.payload[0]["daterange"] == {
        "start_date": "03/01/2024",
        "end_date": "06/28/2024",
    }

    status, response = DashboardEconomic(
        str(farm.id),
        str(pond.id),
        str(cycle.id),
        "06/28/2024",
    ).economic()
    assert status == 200
    assert response.payload["profit_n_lost"]["data"][0]["value"] == 120.0


@pytest.mark.parametrize("date", ["03/31/2024", "06/01/2024"])
def test_seed_demo_supports_feeding_dashboard(date):
    call_command("seed_demo", verbosity=0)

    farm = Farm.objects(user_id="__seed__").order_by("-created_at").first()
    pond = Pond.objects(farm_id=str(farm.id)).first()
    cycle = Cycle.objects(pond_id=str(pond.id)).first()

    status, response = DashboardFeed(
        str(farm.id),
        str(pond.id),
        str(cycle.id),
        date,
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
    call_command("seed_demo", verbosity=0)

    farm = Farm.objects(user_id="__seed__").order_by("-created_at").first()
    pond = Pond.objects(farm_id=str(farm.id)).first()
    cycle = Cycle.objects(pond_id=str(pond.id)).first()
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
        "03/31/2024",
    ).feed()

    assert status == 200, response.message
    realization = next(
        item["data"]
        for item in response.payload["daily_feed_adjustment"]["data"]
        if item["title"] == "Realization"
    )
    assert realization["ration"][0]["ration_number"] == "1"


def test_existing_user_without_dashboard_ready_data_gets_seed_once(monkeypatch):
    call_command("seed_demo", verbosity=0)
    source_farm = Farm.objects(user_id="__seed__").order_by("-created_at").first()
    source_pond = Pond.objects(farm_id=str(source_farm.id)).first()
    source_cycle = Cycle.objects(pond_id=str(source_pond.id)).first()

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
    assert len(response.payload) == 1

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

    assert ensure_default_data_for_user(str(user.id)) is False
    assert Farm.objects(user_id=str(user.id)).count() == farm_count


def test_existing_matching_demo_cycle_is_repaired_in_place(monkeypatch):
    call_command("seed_demo", verbosity=0)
    source_farm = Farm.objects(user_id="__seed__").order_by("-created_at").first()
    source_pond = Pond.objects(farm_id=str(source_farm.id)).first()
    source_cycle = Cycle.objects(pond_id=str(source_pond.id)).first()

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
    assert Cycle.objects(pond_id=str(pond.id)).count() == 1
    assert len(ResultData.objects(cycle_id=str(cycle.id)).first().result_data) == 120
    assert user_has_dashboard_data(str(user.id)) is True


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

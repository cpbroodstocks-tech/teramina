from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from teramina.cost_data.models.cost_data_model import CostData
from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData, ResultData
from teramina.farm.models.farm_model import Farm
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.helpers.management.commands.seed_demo import load_sample_seed_data
from teramina.pond.models.pond_model import Pond


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
    result_rows = load_sample_seed_data(SAMPLE_DATA_DIR)["result_rows"]

    assert all(row["abw"] > 0 for row in result_rows)
    assert all(0 < row["sr"] <= 1 for row in result_rows)
    assert all(row["do"] > 0 for row in result_rows)
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

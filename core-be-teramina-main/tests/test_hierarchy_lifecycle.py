"""Focused hierarchy lifecycle invariants."""

from datetime import datetime, timedelta

import pytest

from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle.services.cycle_service import CycleService
from teramina.dashboard.services.filter_service import FilterData
from teramina.farm.models.farm_model import Farm
from teramina.farm.services.farm_service import FarmService
from teramina.pond.models.pond_model import Pond
from teramina.pond.services.pond_service import PondService


@pytest.fixture(autouse=True)
def clean_hierarchy():
    Farm.objects.delete()
    Pond.objects.delete()
    Cycle.objects.delete()
    yield
    Farm.objects.delete()
    Pond.objects.delete()
    Cycle.objects.delete()


def build_hierarchy():
    farm = Farm(name="Farm", location="Bali", user_id="user-1").save()
    pond = Pond(name="Pond", farm_id=str(farm.id), size=1000).save()
    old_cycle = Cycle(name="Old", pond_id=str(pond.id), start_date=datetime.now() - timedelta(days=30)).save()
    new_cycle = Cycle(name="New", pond_id=str(pond.id), start_date=datetime.now()).save()
    pond.update(set__active_cycle_id=str(new_cycle.id))
    return farm, pond, old_cycle, new_cycle


def test_archiving_active_cycle_repairs_pond_reference():
    _, pond, old_cycle, new_cycle = build_hierarchy()

    CycleService().archive_cycle(str(new_cycle.id), "user-1")

    pond.reload()
    assert pond.active_cycle_id == str(old_cycle.id)


def test_active_cycle_must_belong_to_pond():
    _, pond, _, _ = build_hierarchy()
    other_pond = Pond(name="Other", farm_id=pond.farm_id, size=1000).save()
    other_cycle = Cycle(name="Other", pond_id=str(other_pond.id), start_date=datetime.now()).save()

    status, _ = PondService.set_active_cycle(str(pond.id), str(other_cycle.id))

    assert status == 400


def test_farm_archive_and_restore_cascades_structure():
    farm, pond, old_cycle, new_cycle = build_hierarchy()

    FarmService.archive_farm(str(farm.id), "user-1")
    pond.reload()
    old_cycle.reload()
    assert pond.archived_at is not None
    assert pond.active_cycle_id == ""
    assert old_cycle.archived_at is not None

    FarmService.restore_farm(str(farm.id))
    pond.reload()
    new_cycle.reload()
    assert pond.archived_at is None
    assert new_cycle.archived_at is None
    assert pond.active_cycle_id == str(new_cycle.id)


def test_archived_structure_is_hidden_from_operational_filters():
    farm, _, _, _ = build_hierarchy()

    FarmService.archive_farm(str(farm.id), "user-1")

    assert list(FilterData("user-1").get_list_data_main()) == []

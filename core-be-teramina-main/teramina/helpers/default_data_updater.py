# pylint: disable=no-member
"""Provision the synchronized onboarding demo bundle for signed-in users."""

import copy
import logging
import os
from datetime import date, datetime, timedelta

import pandas as pd
from mongoengine.errors import ValidationError

from ..cost_data.models.cost_data_model import CostData
from ..cycle.models.cycle_model import Cycle
from ..cycle_data.models.cycle_data_model import CycleData, ForecastData, ResultData
from ..dashboard.services.readiness import is_dashboard_ready_cycle
from ..farm.models.farm_model import Farm
from ..feeding.models.feed_realization_model import FeedRealization
from ..harvest.models.harvest_record_model import HarvestRecord
from ..harvest.models.harvest_recommendation_model import HarvestRecommendation
from ..helpers.demo_artifacts import DEMO_BUNDLE_VERSION, seed_user_demo_artifacts
from ..helpers.pinecone_data_indexing import PineconeIndexing
from ..pond.models.pond_model import Pond
from ..user.models.user_model import User


logger = logging.getLogger("teramina")
CURRENT_DOC = 60


def user_has_dashboard_data(user_id):
    """Return whether a user owns at least one cycle usable by the dashboard."""
    farm_ids = [str(farm.id) for farm in Farm.objects(user_id=str(user_id)).only("id")]
    if not farm_ids:
        return False
    pond_ids = [str(pond.id) for pond in Pond.objects(farm_id__in=farm_ids).only("id")]
    if not pond_ids:
        return False
    cycle_ids = [str(cycle.id) for cycle in Cycle.objects(pond_id__in=pond_ids).only("id")]
    return any(is_dashboard_ready_cycle(cycle_id) for cycle_id in cycle_ids)


def sync_user_data_status(user_id):
    """Repair the cached data-status flag from actual dashboard-ready records."""
    has_data = user_has_dashboard_data(user_id)
    User.objects(id=user_id).update(set__is_there_data=has_data)
    return has_data


def ensure_default_data_for_user(user_id):
    """Clone the configured onboarding bundle only when the user lacks usable data."""
    if sync_user_data_status(user_id):
        return False
    seed_ids = (os.getenv("SEEDER_FARM"), os.getenv("SEEDER_POND"), os.getenv("SEEDER_CYCLE"))
    try:
        source_farm = Farm.objects(id=seed_ids[0]).first() if seed_ids[0] else None
    except ValidationError:
        source_farm = None
    source_farm = source_farm or Farm.objects(
        user_id="__seed__",
        demo_bundle_version=DEMO_BUNDLE_VERSION,
    ).order_by("-created_at").first()
    if not source_farm:
        return False
    seeder = DataSeeder(str(source_farm.id), seed_ids[1], seed_ids[2], user_id=str(user_id))
    if not seeder.repair_existing_data():
        seeder.set_data()
    return sync_user_data_status(user_id)


def _rebase_rows(rows, start_date, date_as_string=False):
    rebased = copy.deepcopy(rows or [])
    for row in rebased:
        doc = row.get("doc")
        if not doc:
            continue
        value = start_date + timedelta(days=int(doc) - 1)
        row["date"] = value.strftime("%Y-%m-%d") if date_as_string else value
    return rebased


class DataSeeder:
    """Clone every pond/cycle under the configured seed farm."""

    def __init__(self, farm_id, pond_id=None, cycle_id=None, user_id=""):
        self.farm_id = farm_id
        self.pond_id = pond_id
        self.cycle_id = cycle_id
        self.user_id = user_id

    def _source_farm(self):
        farm = Farm.objects(id=self.farm_id).first()
        if not farm:
            raise ValueError("Configured onboarding seed farm does not exist")
        return farm

    def _source_ponds(self):
        ponds = list(Pond.objects(farm_id=self.farm_id).order_by("name"))
        if not ponds:
            raise ValueError("Configured onboarding seed farm has no ponds")
        return ponds

    @staticmethod
    def _source_cycle(pond_id):
        pond = Pond.objects(id=pond_id).first()
        cycle = Cycle.objects(id=pond.active_cycle_id, pond_id=pond_id).first() if pond and pond.active_cycle_id else None
        cycle = cycle or Cycle.objects(pond_id=pond_id).order_by("-start_date").first()
        if not cycle:
            raise ValueError(f"Configured onboarding seed pond {pond_id} has no cycle")
        return cycle

    @staticmethod
    def _delete_pond_children(pond):
        for cycle in Cycle.objects(pond_id=str(pond.id)):
            cycle_id = str(cycle.id)
            CycleData.objects(cycle_id=cycle_id).delete()
            ResultData.objects(cycle_id=cycle_id).delete()
            ForecastData.objects(cycle_id=cycle_id).delete()
            FeedRealization.objects(cycle_id=cycle_id).delete()
            HarvestRecord.objects(cycle_id=cycle_id).delete()
            HarvestRecommendation.objects(cycle_id=cycle_id).delete()
            CostData.objects(farm_id=cycle_id).delete()
            cycle.delete()
        pond.delete()

    def _clone_cycle(self, source_cycle, target_pond, farm_info):
        now = datetime.utcnow()
        start_date = datetime.combine(date.today() - timedelta(days=CURRENT_DOC - 1), datetime.min.time())
        target_cycle = Cycle(
            name=source_cycle.name,
            start_date=start_date,
            pond_id=str(target_pond.id),
            demo_scenario=source_cycle.demo_scenario,
            is_active=True,
            last_updated=now,
        ).save()
        cycle_id = str(target_cycle.id)
        target_pond.active_cycle_id = cycle_id
        target_pond.save()

        source_cycle_data = CycleData.objects(cycle_id=str(source_cycle.id)).first()
        source_result_data = ResultData.objects(cycle_id=str(source_cycle.id)).first()
        source_forecast_data = ForecastData.objects(cycle_id=str(source_cycle.id)).first()
        if not source_cycle_data or not source_cycle_data.result_data or not source_result_data or not source_result_data.result_data:
            raise ValueError(f"Configured onboarding seed cycle {source_cycle.id} is incomplete")

        cycle_rows = _rebase_rows(source_cycle_data.result_data, start_date, date_as_string=True)
        result_rows = _rebase_rows(source_result_data.result_data, start_date)
        forecast_rows = _rebase_rows(source_forecast_data.result_data if source_forecast_data else [], start_date)
        CycleData(cycle_id=cycle_id, result_data=cycle_rows, last_updated=now).save()
        ResultData(cycle_id=cycle_id, result_data=result_rows, last_updated=now).save()
        ForecastData(cycle_id=cycle_id, result_data=forecast_rows, last_updated=now).save()

        for feed in FeedRealization.objects(cycle_id=str(source_cycle.id)):
            FeedRealization(
                cycle_id=cycle_id,
                doc=feed.doc,
                ration_number=feed.ration_number,
                feed_ration=feed.feed_ration,
                feed_given=feed.feed_given,
                feed_leftover=feed.feed_leftover,
                last_updated=now,
            ).save()

        source_harvest = HarvestRecord.objects(cycle_id=str(source_cycle.id)).first()
        if source_harvest:
            HarvestRecord(cycle_id=cycle_id, harvest_data=copy.deepcopy(source_harvest.harvest_data), last_updated=now).save()
        source_recommendation = HarvestRecommendation.objects(cycle_id=str(source_cycle.id)).first()
        if source_recommendation:
            HarvestRecommendation(
                cycle_id=cycle_id,
                harvest_data=copy.deepcopy(source_recommendation.harvest_data),
                last_updated=now,
            ).save()

        source_cost = CostData.objects(farm_id=str(source_cycle.id)).first()
        if source_cost:
            cost_rows = copy.deepcopy(source_cost.data or [])
            for row in cost_rows:
                old_date = row.get("date")
                try:
                    old_date = datetime.fromisoformat(str(old_date)).date()
                    old_start = source_cycle.start_date.date()
                    doc = (old_date - old_start).days + 1
                    row["date"] = (start_date + timedelta(days=doc - 1)).strftime("%Y-%m-%d")
                except (TypeError, ValueError):
                    pass
            CostData(
                farm_id=cycle_id,
                start_date=cycle_rows[0]["date"],
                end_date=cycle_rows[-1]["date"],
                data=cost_rows,
                last_updated=now,
            ).save()

        try:
            frame = pd.DataFrame(cycle_rows).assign(
                **farm_info,
                pond_id=str(target_pond.id),
                pond_name=target_pond.name,
                cycle_id=cycle_id,
                cycle_name=target_cycle.name,
                cycle_start_date=start_date,
            )
            PineconeIndexing(str(self.user_id)).create_index(frame)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Onboarding Pinecone indexing skipped for user %s: %s", self.user_id, exc)

        return {
            "pond_id": str(target_pond.id),
            "pond_name": target_pond.name,
            "cycle_id": cycle_id,
            "cycle_name": target_cycle.name,
        }

    def _populate_farm(self, target_farm):
        for pond in list(Pond.objects(farm_id=str(target_farm.id))):
            self._delete_pond_children(pond)

        scenarios = {}
        farm_info = {
            "farm_id": str(target_farm.id),
            "farm_name": target_farm.name,
            "farm_location": target_farm.location,
        }
        for source_pond in self._source_ponds():
            target_pond = Pond(
                name=source_pond.name,
                size=source_pond.size,
                depth=source_pond.depth,
                pond_construction=source_pond.pond_construction,
                pond_shape=source_pond.pond_shape,
                farm_id=str(target_farm.id),
                demo_scenario=source_pond.demo_scenario,
                is_active=True,
            ).save()
            cloned = self._clone_cycle(self._source_cycle(str(source_pond.id)), target_pond, farm_info)
            scenarios[source_pond.demo_scenario or "healthy"] = cloned

        if "healthy" not in scenarios or "at_risk" not in scenarios:
            raise ValueError("Configured onboarding bundle must contain healthy and at_risk scenarios")
        seed_user_demo_artifacts(self.user_id, str(target_farm.id), scenarios)
        User.objects(id=self.user_id).update(set__is_there_data=True)

    def repair_existing_data(self):
        """Replace an older matching demo farm in place, preserving its farm ID."""
        source_farm = self._source_farm()
        target = Farm.objects(user_id=self.user_id, demo_bundle_version=DEMO_BUNDLE_VERSION).first()
        target = target or Farm.objects(user_id=self.user_id, name__in=[source_farm.name, "Demo Farm"]).first()
        if not target:
            return False
        target.name = source_farm.name
        target.location = source_farm.location
        target.demo_bundle_version = DEMO_BUNDLE_VERSION
        target.last_updated = datetime.utcnow()
        target.save()
        self._populate_farm(target)
        return True

    def set_data(self):
        """Clone the complete seed bundle into a new user-owned farm."""
        source_farm = self._source_farm()
        target = Farm(
            name=source_farm.name,
            location=source_farm.location,
            user_id=self.user_id,
            demo_bundle_version=DEMO_BUNDLE_VERSION,
            last_updated=datetime.utcnow(),
        ).save()
        self._populate_farm(target)

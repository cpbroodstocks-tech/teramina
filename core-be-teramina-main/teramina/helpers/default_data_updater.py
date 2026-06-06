# pylint: disable=no-member
"""Default data setuper"""

import logging
import os
import pandas as pd
from datetime import datetime

from ..farm.models.farm_model import Farm
from ..pond.models.pond_model import Pond
from ..cycle.models.cycle_model import Cycle
from ..cycle_data.models.cycle_data_model import CycleData, ResultData, ForecastData
from ..harvest.models.harvest_record_model import HarvestRecord
from ..feeding.models.feed_realization_model import FeedRealization
from ..cost_data.models.cost_data_model import CostData
from ..user.models.user_model import User

from ..helpers.pinecone_data_indexing import PineconeIndexing


logger = logging.getLogger("teramina")

DASHBOARD_REQUIRED_FIELDS = {
    "date",
    "doc",
    "category",
    "adj_abw",
    "sr",
    "initial_stocking",
    "harvest_biomass_kg",
    "biomass_kg",
    "total_biomass",
    "potential_revenue",
    "cum_total_cost",
    "cost_per_kg",
    "cost_harvest",
    "cost_energy",
    "cost_probiotics",
    "cost_other",
    "cost_labor",
    "cost_bonuss",
    "cost_feed",
}


def user_has_dashboard_data(user_id):
    """Return whether a user owns at least one cycle usable by the dashboard."""
    farm_ids = [str(farm.id) for farm in Farm.objects(user_id=str(user_id)).only("id")]
    if not farm_ids:
        return False

    pond_ids = [str(pond.id) for pond in Pond.objects(farm_id__in=farm_ids).only("id")]
    if not pond_ids:
        return False

    cycle_ids = [str(cycle.id) for cycle in Cycle.objects(pond_id__in=pond_ids).only("id")]
    for cycle_id in cycle_ids:
        cycle_data = CycleData.objects(cycle_id=cycle_id).only("result_data").first()
        result_data = ResultData.objects(cycle_id=cycle_id).only("result_data").first()
        if not cycle_data or not cycle_data.result_data or not result_data or not result_data.result_data:
            continue
        last_result = result_data.result_data[-1]
        if isinstance(last_result, dict) and DASHBOARD_REQUIRED_FIELDS.issubset(last_result.keys()):
            return True

    return False


def sync_user_data_status(user_id):
    """Repair the cached data-status flag from actual dashboard-ready records."""
    has_data = user_has_dashboard_data(user_id)
    User.objects(id=user_id).update(set__is_there_data=has_data)
    return has_data


def ensure_default_data_for_user(user_id):
    """Clone the configured onboarding seed only when the user lacks usable data."""
    if sync_user_data_status(user_id):
        return False

    seed_ids = (
        os.getenv("SEEDER_FARM"),
        os.getenv("SEEDER_POND"),
        os.getenv("SEEDER_CYCLE"),
    )
    if not all(seed_ids):
        return False

    seeder = DataSeeder(*seed_ids, user_id=str(user_id))
    if not seeder.repair_existing_data():
        seeder.set_data()
    return sync_user_data_status(user_id)


class DataSeeder:
    """Data Seeder"""

    def __init__(self, farm_id, pond_id, cycle_id, user_id):
        """data initialization"""
        self.farm_id = farm_id
        self.pond_id = pond_id
        self.cycle_id = cycle_id
        self.user_id = user_id

    def set_farm(self):
        """farm setup"""
        farm = Farm.objects(id=self.farm_id).first()
        farm_name = farm.name
        farm_loc = farm.location
        new_farm = Farm(name=farm_name, location=farm_loc, user_id=self.user_id)
        new_farm.save()
        data = {
            "farm_name": farm_name,
            "farm_location": farm_loc,
            "farm_id": str(new_farm.id),
        }
        return data

    def set_pond(self):
        """pond setup"""
        farm_data = self.set_farm()
        pond = Pond.objects(id=self.pond_id).first()
        pond_name = pond.name
        pond_size = pond.size
        pond_depth = pond.depth
        pond_construction = pond.pond_construction
        pond_shape = pond.pond_shape
        new_pond = Pond(
            name=pond_name,
            size=pond_size,
            depth=pond_depth,
            pond_construction=pond_construction,
            pond_shape=pond_shape,
            farm_id=farm_data["farm_id"],
        )
        new_pond.save()
        data = {
            "pond_id": str(new_pond.id),
            "pond_name": pond_name,
            "pond_size": pond_size,
            "pond_depth": pond_depth,
            "pond_construction": pond_construction,
            "pond_shape": pond_shape,
        }

        data.update(farm_data)
        return data

    def set_cycle(self):
        """cycle stup"""
        pond_data = self.set_pond()
        cycle = Cycle.objects(id=self.cycle_id).first()
        cycle_name = cycle.name
        cycle_start_date = cycle.start_date
        new_cycle = Cycle(
            name=cycle_name, start_date=cycle_start_date, pond_id=pond_data["pond_id"]
        )
        new_cycle.save()
        Pond.objects(id=pond_data["pond_id"]).update(set__active_cycle_id=str(new_cycle.id))

        data = {
            "cycle_name": cycle_name,
            "cycle_start_date": cycle_start_date,
            "cycle_id": str(new_cycle.id),
        }
        data.update(pond_data)
        return data

    def _get_source_documents(self):
        """Load and validate the configured source cycle documents."""
        cycle_data = CycleData.objects(cycle_id=self.cycle_id).first()
        result_data = ResultData.objects(cycle_id=self.cycle_id).first()
        forecast_data = ForecastData.objects(cycle_id=self.cycle_id).first()
        if not cycle_data or not cycle_data.result_data or not result_data or not result_data.result_data:
            raise ValueError("Configured onboarding seed is incomplete")
        return cycle_data, result_data, forecast_data

    def _copy_cycle_documents(self, cycle_data_info):
        """Replace one target cycle's documents with the configured source data."""
        cycle_id = cycle_data_info["cycle_id"]
        now = datetime.utcnow()
        cycle_data, result_data, forecast_data = self._get_source_documents()

        CycleData.objects(cycle_id=cycle_id).delete()
        ResultData.objects(cycle_id=cycle_id).delete()
        ForecastData.objects(cycle_id=cycle_id).delete()
        FeedRealization.objects(cycle_id=cycle_id).delete()
        HarvestRecord.objects(cycle_id=cycle_id).delete()
        CostData.objects(farm_id=cycle_id).delete()

        # ── Core cycle documents ───────────────────────────────────────────
        CycleData(cycle_id=cycle_id, result_data=cycle_data.result_data, last_updated=now).save()
        ResultData(cycle_id=cycle_id, result_data=result_data.result_data, last_updated=now).save()
        ForecastData(cycle_id=cycle_id, result_data=forecast_data.result_data if forecast_data else [], last_updated=now).save()

        # ── Feeding records ────────────────────────────────────────────────
        for fr in FeedRealization.objects(cycle_id=self.cycle_id):
            FeedRealization(
                cycle_id=cycle_id,
                doc=fr.doc,
                ration_number=fr.ration_number,
                feed_ration=fr.feed_ration,
                feed_given=fr.feed_given,
                feed_leftover=fr.feed_leftover,
                last_updated=now,
            ).save()

        # ── Harvest records ────────────────────────────────────────────────
        for hr in HarvestRecord.objects(cycle_id=self.cycle_id):
            HarvestRecord(
                cycle_id=cycle_id,
                harvest_data=hr.harvest_data,
                last_updated=now,
            ).save()

        # ── Cost data ──────────────────────────────────────────────────────
        src_cost = CostData.objects(farm_id=self.cycle_id).first()
        if src_cost:
            CostData(
                farm_id=cycle_id,
                start_date=src_cost.start_date,
                end_date=src_cost.end_date,
                data=src_cost.data,
                last_updated=now,
            ).save()

        # ── Mark user as having data ───────────────────────────────────────
        User.objects(id=self.user_id).update(set__is_there_data=True)

        # ── Pinecone indexing ──────────────────────────────────────────────
        if cycle_data.result_data:
            df = pd.DataFrame(cycle_data.result_data)
            df = df.assign(**cycle_data_info)
            try:
                PineconeIndexing(str(self.user_id)).create_index(df)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Onboarding Pinecone indexing skipped for user %s: %s", self.user_id, exc)

    def repair_existing_data(self):
        """Repair an older matching demo clone in place, preserving its IDs."""
        source_farm = Farm.objects(id=self.farm_id).first()
        source_pond = Pond.objects(id=self.pond_id).first()
        source_cycle = Cycle.objects(id=self.cycle_id).first()
        if not source_farm or not source_pond or not source_cycle:
            raise ValueError("Configured onboarding seed farm, pond, or cycle does not exist")

        farms = Farm.objects(
            user_id=self.user_id,
            name=source_farm.name,
            location=source_farm.location,
        )
        for farm in farms:
            pond = Pond.objects(farm_id=str(farm.id), name=source_pond.name).first()
            if not pond:
                continue
            cycle = Cycle.objects(pond_id=str(pond.id), name=source_cycle.name).first()
            if not cycle:
                continue

            cycle.start_date = source_cycle.start_date
            cycle.is_active = True
            cycle.last_updated = datetime.utcnow()
            cycle.save()
            pond.active_cycle_id = str(cycle.id)
            pond.save()

            self._copy_cycle_documents(
                {
                    "farm_name": farm.name,
                    "farm_location": farm.location,
                    "farm_id": str(farm.id),
                    "pond_id": str(pond.id),
                    "pond_name": pond.name,
                    "pond_size": pond.size,
                    "pond_depth": pond.depth,
                    "pond_construction": pond.pond_construction,
                    "pond_shape": pond.pond_shape,
                    "cycle_name": cycle.name,
                    "cycle_start_date": cycle.start_date,
                    "cycle_id": str(cycle.id),
                }
            )
            return True

        return False

    def set_data(self):
        """Clone the configured seed into a new farm, pond, and cycle."""
        self._get_source_documents()
        self._copy_cycle_documents(self.set_cycle())

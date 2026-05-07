# pylint: disable=no-member
"""Default data setuper"""

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

        data = {
            "cycle_name": cycle_name,
            "cycle_start_date": cycle_start_date,
            "cycle_id": str(new_cycle.id),
        }
        data.update(pond_data)
        return data

    def set_data(self):
        """set data"""
        cycle_data_info = self.set_cycle()
        cycle_id = cycle_data_info["cycle_id"]
        now = datetime.utcnow()

        # ── Core cycle documents ───────────────────────────────────────────
        cycle_data = CycleData.objects(cycle_id=self.cycle_id).first()
        result_data = ResultData.objects(cycle_id=self.cycle_id).first()
        forecast_data = ForecastData.objects(cycle_id=self.cycle_id).first()

        CycleData(cycle_id=cycle_id, result_data=cycle_data.result_data if cycle_data else [], last_updated=now).save()
        ResultData(cycle_id=cycle_id, result_data=result_data.result_data if result_data else [], last_updated=now).save()
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
                data=src_cost.data,
                last_updated=now,
            ).save()

        # ── Mark user as having data ───────────────────────────────────────
        User.objects(id=self.user_id).update(set__is_there_data=True)

        # ── Pinecone indexing ──────────────────────────────────────────────
        if cycle_data and cycle_data.result_data:
            df = pd.DataFrame(cycle_data.result_data)
            df = df.assign(**cycle_data_info)
            PineconeIndexing(str(self.user_id)).create_index(df)

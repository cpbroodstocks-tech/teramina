"""farm data collecting by cycle id"""

from teramina.cycle.models.cycle_model import Cycle
from teramina.pond.models.pond_model import Pond
from teramina.farm.models.farm_model import Farm


def get_data(cycle_id):
    """get data from cycle id"""
    cycle_data = Cycle.objects(id=cycle_id).first()
    if cycle_data:
        pond_data = Pond.objects(id=cycle_data.pond_id).first()
        farm_data = Farm.objects(id=pond_data.farm_id).first()

        if pond_data and farm_data:
            result = {
                "cycle_id": str(cycle_id),
                "cycle_name": cycle_data.name,
                "cycle_start_date": str(cycle_data.start_date),
                "pond_id": str(pond_data.id),
                "pond_name": pond_data.name,
                "pond_size": pond_data.size,
                "pond_construction": pond_data.pond_construction,
                "pond_shape": pond_data.pond_shape,
                "farm_id": str(farm_data.id),
                "farm_name": farm_data.name,
                "farm_location": farm_data.location,
            }

            return result
    return None


def combine_with_df(cycle_id, df):
    """combine with dataframe"""
    data = get_data(cycle_id)
    if data:
        df = df.assign(**data)

    return df

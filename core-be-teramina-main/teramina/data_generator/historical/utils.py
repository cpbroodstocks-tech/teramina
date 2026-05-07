import pandas as pd

from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.feeding.models.feed_realization_model import FeedRealization

from teramina.formulas.cost.cost_formula import Cost


def parse_tray_data_input(data: FeedRealization):
    """parsing tray data input

    Args:
        data (list): _description_

    Returns:
        _type_: _description_
    """
    new_data = [{"doc": i.doc, "tray": i.feed_leftover} for i in data]
    return pd.DataFrame(new_data)


def set_carriying_capacity(df, cycle_id: str, cost: Cost):
    """set carriying capacity into the dataframe"""
    cycle = Cycle.objects(id=cycle_id).only("pond_id").first()
    pond = Pond.objects(id=cycle.pond_id).only("size", "depth").first()
    df["carriying_capacity"] = cost.get_carriying_capacity_values(
        area=pond.size, depth=pond.depth
    )
    return df

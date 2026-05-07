"""
Shrimp price data updater

"""

import requests
import numpy as np
import pandas as pd

from ..pond.models.pond_model import Pond
from ..cycle.models.cycle_model import Cycle
from ..farm.models.farm_model import Farm
from .constant_value import Constant


def update_price_table(location: str):
    """update price table

    Args:
        location (str): farm location

    Returns:
        list | None: price data, or None if the service is unreachable
    """
    base_url = "https://shrimp-price-service-94567199226.asia-southeast2.run.app/api"
    try:
        resp = requests.get(
            f"{base_url}/price/get_price_by_location?location={location}", timeout=10
        )
        resp.raise_for_status()
        return resp.json()["payload"]["data"]
    except Exception:  # pylint: disable=broad-except
        # Price service is optional — do not block farm creation if it's unavailable
        return None


def get_cycle_details(cycle_id: str):
    """Generate farm's info

    Args:
        cycle_id (str): cycle id
    """
    cycle = Cycle.objects(id=cycle_id).first()
    pond = Pond.objects(id=cycle.pond_id).first()
    farm = Farm.objects(id=pond.farm_id).first()

    return {
        "cycle_id": str(cycle.id),
        "pond_id": str(pond.id),
        "farm_id": str(farm.id),
        "farm_name": farm.name,
        "farm_location": farm.location,
        "pond_name": pond.name,
        "pond_size": pond.size,
        "pond_depth": pond.depth,
        "pond_construction": pond.pond_construction,
        "pond_shape": pond.pond_shape,
        "cycle_name": cycle.name,
        "cycle_start_date": cycle.start_date,
    }


def price_converter(data: list[dict]):
    """prive converter list[dict] into array

    Args:
        data (list[dict]): example of data [{size: 20, price: 100000}]
    """

    data = np.array([list(i.values()) for i in data])
    return data


def _fallback_price_array() -> np.ndarray:
    """Load the local preprocessed price table when the price service is unavailable."""
    df = pd.read_csv(Constant.SHRIMP_PRICE_ARRAY_PATH, header=None)
    return df.values.astype(float)


def get_price_array(cycle_id: str):
    """get price array data

    Args:
        cycle_id (str): cycle id
    """
    data = update_price_table(get_cycle_details(cycle_id)["farm_location"])
    if data is None:
        return _fallback_price_array()
    return price_converter(data)

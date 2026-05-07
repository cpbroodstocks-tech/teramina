from datetime import datetime
import pandas as pd
import numpy as np

from mongoengine.errors import LookUpError, InvalidQueryError

from ..cycle_data.models.cycle_data_model import ResultData, ForecastData
from ..pond.models.pond_model import Pond
from ..farm.models.farm_model import Farm
from ..cycle.models.cycle_model import Cycle


def update_historical_data_result(cycle_id: str, ndf: pd.DataFrame):
    """update historical data result

    Args:
        cycle_id (str): cycle id
        ndf (pd.DataFrame): historical farming data

    Raises:
        LookUpError: Some required data was not found
        InvalidQueryError: Something wrong with the query
    """
    try:
        ndf = ndf.where(pd.notnull(ndf), None)
        ndf = ndf.replace({np.nan: None})
        array_data = ndf.to_dict("records")

        result_data = ResultData.objects(cycle_id=cycle_id).first()
        if result_data:
            result_data.result_data = array_data
            result_data.save()
        else:
            ResultData(cycle_id=cycle_id, result_data=array_data).save()

    except (LookUpError, InvalidQueryError) as exc:
        raise type(exc)("Some required data was not found") from exc


def update_forecast_combined_data_result(cycle_id: str, ndf: pd.DataFrame):
    """update forecaset combined data result

    Args:
        cycle_id (str): cycle id
        ndf (pd.DataFrame): historical farming data

    Raises:
        LookUpError: Some required data was not found
        InvalidQueryError: Something wrong with the query
    """
    try:
        ndf = ndf.where(pd.notnull(ndf), None)
        ndf = ndf.replace({np.nan: None})
        array_data = ndf.to_dict("records")

        result_data = ForecastData.objects(cycle_id=cycle_id).first()
        if result_data:
            result_data.result_data = array_data
            result_data.save()
        else:
            ForecastData(cycle_id=cycle_id, result_data=array_data).save()
    except (LookUpError, InvalidQueryError) as exc:
        raise type(exc)("Some required data was not found") from exc


def set_last_updated(cycle_id):
    """set last datetime updated data"""
    try:
        cycle = Cycle.objects(id=str(cycle_id)).only("pond_id").first()
        pond_id = str(cycle.pond_id)
        pond = Pond.objects(id=pond_id).only("farm_id").first()
        farm_id = str(pond.farm_id)

        last_update = datetime.now()
        Farm.objects(id=farm_id).update(set__last_updated=last_update)
        Pond.objects(id=pond_id).update(set__last_updated=last_update)
        Cycle.objects(id=cycle_id).update(set__last_updated=last_update)
    except (LookUpError, InvalidQueryError) as exc:
        raise type(exc)(
            "Something wrong with the query for the farm, pond, or cycle table"
        ) from exc

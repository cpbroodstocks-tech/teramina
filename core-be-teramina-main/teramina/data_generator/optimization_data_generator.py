# pylint: disable=R0801, E1137

import numpy as np

from teramina.formulas.harvest_optimization_formula import Optimization
from teramina.data_generator.forecast.forecast_data_dummy_generator import ForecastData
from teramina.data_generator.helpers.utils import (
    parse_harvest_data_input,
    set_params_config,
)

from ..helpers.constant_column import Column
from ..helpers.constant_value import Constant
from ..helpers.shrimp_price import get_price_array

from ..harvest.models.harvest_record_model import HarvestRecord
from .historical.historical_data_generator import HistoricalDataGenerator


class OptimalDataGenerator(HistoricalDataGenerator):
    """Optimal Data Generator"""

    def __init__(self, cycle_id) -> None:
        self.cycle_id = cycle_id

        super().__init__(cycle_id)

    def __parse_forecast_data(
        self, historical_partial_doc, optimal_ph, optimal_partial_doc
    ):
        historical_partial_doc = np.array(historical_partial_doc)
        optimal_ph = np.array(optimal_ph)
        optimal_partial_doc = np.array(optimal_partial_doc)

        forecast_index = np.where(~np.isin(optimal_partial_doc, historical_partial_doc))
        forecast_ph = optimal_ph[forecast_index]
        forecast_partial_doc = optimal_partial_doc[forecast_index]

        return {
            "forecast_ph": forecast_ph,
            "forecast_partial_doc": forecast_partial_doc,
        }

    def __get_data(self, historical_df):
        harvest = (
            HarvestRecord.objects(cycle_id=self.cycle_id).only("harvest_data").first()
        )
        if harvest:
            harvest_data = parse_harvest_data_input(harvest.harvest_data)
            ph = harvest_data["partial_harvest"]
            partial_doc = harvest_data["partial_doc"]
        else:
            ph = []
            partial_doc = []

        # generate forecasted data
        forecast_object = ForecastData.get_forecast_df(historical_df)

        # set the parameter for the historical data
        (
            init_data,
            population_config,
            growth_config,
            cost_config,
        ) = set_params_config(
            historical_df,
            ph,
            partial_doc,
            forecast_object["historical_docfinal"],
        )

        # initialize the forecase dataframe
        forecast_df = forecast_object["table"]
        forecast_df["abw"] = np.nan

        # restructuring the growth config
        growth_config["t"] = forecast_object["historical_docfinal"]
        growth_config["t0"] = 0
        growth_config["protein_content"] = init_data["protein_content"]

        opt_object = Optimization(
            historical_df=historical_df,
            forecast_df=forecast_df,
            growth_config=growth_config,
            population_config=population_config,
            cost_config=cost_config,
            temperature_fr_array=np.loadtxt(
                Constant.FR_TEMPERATURE_ARRAY_PATH, delimiter=","
            ),
            price_array=get_price_array(self.cycle_id),
            required_columns=Column.dependent_columns,
            is_ph_as_biomass=True,
        )

        optimal_ph, optimal_partial_doc = opt_object.get_optimal_harvest()
        return ph, partial_doc, optimal_ph, optimal_partial_doc

    def get_optimal_harvest(self, historical_df):
        """Get optimal harvest data"""

        ph, partial_doc, optimal_ph, optimal_partial_doc = self.__get_data(
            historical_df
        )

        forecast_harvest_info = self.__parse_forecast_data(
            partial_doc, optimal_ph, optimal_partial_doc
        )

        if list(forecast_harvest_info["forecast_partial_doc"]):
            doc_final = forecast_harvest_info["forecast_partial_doc"][-1]
            part_doc_without_final = forecast_harvest_info["forecast_partial_doc"][:-1]
            part_harvest_without_final = forecast_harvest_info["forecast_ph"][:-1]
        else:
            doc_final = Constant.MAX_DOC
            part_doc_without_final = []
            part_harvest_without_final = []

        return {
            "optimal_ph": optimal_ph,
            "optimal_partial_doc": optimal_partial_doc,
            "historical_ph": ph,
            "historical_partial_doc": partial_doc,
            "forecast_ph": forecast_harvest_info["forecast_ph"],
            "forecast_partial_doc": forecast_harvest_info["forecast_partial_doc"],
            "doc_final": doc_final,
            "forecast_partial_doc_without_final_doc": part_doc_without_final,
            "forecast_partial_harvest_without_final_doc": part_harvest_without_final,
        }

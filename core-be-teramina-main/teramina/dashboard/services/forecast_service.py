# pylint: disable=too-few-public-methods, E0401

import copy
import numpy as np
import pandas as pd

from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.cycle_data.models.cycle_data_model import ForecastData
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from teramina.helpers.plot import LineForecast
from teramina.data_generator.combined_data_simulator import CombinedDataSimulator
from teramina.helpers.constant_value import Constant
from teramina.dashboard.services.dashboard_utils import get_max_filter_doc


class ForecastDataService:
    """service that lead to forecasted data"""

    def __get_harvest_recommendation(self, cycle_id):
        harvest = HarvestRecommendation.objects(cycle_id=cycle_id).first()
        if harvest:
            return harvest.harvest_data

        return None

    def __get_adjusted_harvest_data(self, cycle_id, origin_harvest_data, max_doc):
        forecasted_harvest_data = self.__get_harvest_recommendation(cycle_id)
        harvest_data = copy.copy(origin_harvest_data)

        if forecasted_harvest_data:
            data = (
                ForecastData.objects(cycle_id=cycle_id)
                .only("result_data")
                .first()
                .result_data
            )
            index = forecasted_harvest_data.keys()

            for i in index:
                harvest_type = "".join(filter(str.isalpha, i))
                if (
                    harvest_type == "partial"
                    and forecasted_harvest_data[i]["doc"] != ""
                    and forecasted_harvest_data[i]["doc"] <= max_doc
                ):
                    harvest_data[i] = {
                        "doc": forecasted_harvest_data[i]["doc"],
                        "biomass": (
                            forecasted_harvest_data[i]["biomass"]
                            * data[forecasted_harvest_data[i]["doc"] - 1]["adj_abw"]
                        )
                        / 1000,
                    }

            return harvest_data

        return harvest_data

    def __generate_forecast(self, cycle_id=None, max_doc=None) -> pd.DataFrame:
        if not max_doc:
            max_doc = Constant.MAX_DOC

        harvest = HarvestRecord.objects(cycle_id=cycle_id).first()
        if harvest:
            harvest_data = harvest.harvest_data
            harvest_data["final"]["doc"] = max_doc
        else:
            harvest_data = {
                "partial1": {"doc": "", "biomass": ""},
                "partial2": {"doc": "", "biomass": ""},
                "partial3": {"doc": "", "biomass": ""},
                "final": {"doc": max_doc, "biomass": ""},
            }
        try:
            harvest_data = self.__get_adjusted_harvest_data(
                cycle_id, harvest_data, max_doc
            )
        except IndexError as exc:
            raise IndexError(
                "Since you have entered the final harvest data, you cannot input forecast data."
            ) from exc

        df = CombinedDataSimulator(cycle_id, harvest_data).generate_simulation_data(
            False
        )
        return df

    def get_forecasting_overview(self, cycle_id=None, date=None):
        """main function to get forecasted data"""
        try:
            max_doc = get_max_filter_doc(cycle_id, False, date)
            if max_doc == 0:
                raise KeyError("Can't simulate historical data, for DOC = 0")

            df = self.__generate_forecast(cycle_id, max_doc)

            historical_df = df.query("category == 'historical' ")
            forecast_df = df.query("category == 'forecast' ")

            if forecast_df.empty:
                raise ValueError(
                    "Since you have entered the final harvest data, you cannot input forecast data."
                )

            historical_df["abw"] = historical_df["abw"].round(2)
            historical_df["origin_biomass"] = historical_df["origin_biomass"].round(2)
            historical_df["biomass_kg"] = historical_df["biomass_kg"].round(2)
            historical_df["harvest_biomass_kg"] = historical_df[
                "harvest_biomass_kg"
            ].round(2)
            historical_df["cum_realized_revenue"] = historical_df[
                "cum_realized_revenue"
            ].round()
            historical_df["profit"] = historical_df["profit"].round()

            historical_df.replace(np.nan, None, inplace=True)

            # plot
            forecast_abw = LineForecast(
                title="ABW",
                x=df["doc"].tolist(),
                y=[
                    historical_df["abw"].tolist()
                    + forecast_df["adj_abw"].round(2).tolist()
                ],
                betweenes_index=int(historical_df["doc"].max() - 1),
                labels=[["origin", "predicted"]],
                legend=False,
                base_color="#474DA4",
                forecast_color="#FBBC05",
            ).plot()

            forecast_biomass = LineForecast(
                title="Biomass",
                x=df["doc"].tolist(),
                y=[
                    historical_df["origin_biomass"].tolist()
                    + forecast_df["biomass_kg"].iloc[:-1].tolist()
                    + [df["harvest_biomass_kg"].iloc[-1]]
                ],
                betweenes_index=int(historical_df["doc"].max() - 1),
                labels=[["origin", "predicted"]],
                legend=False,
                base_color="#474DA4",
                forecast_color="#FBBC05",
            ).plot()

            forecast_revenue = LineForecast(
                title="Revenue",
                x=df["doc"].tolist(),
                y=[
                    historical_df["cum_realized_revenue"].tolist()
                    + forecast_df["cum_realized_revenue"].round().tolist()
                ],
                betweenes_index=int(historical_df["doc"].max()),
                labels=[["origin", "predicted"]],
                legend=False,
                base_color="#474DA4",
                forecast_color="#FBBC05",
            ).plot()

            forecast_profit = LineForecast(
                title="Profit",
                x=df["doc"].tolist(),
                y=[
                    historical_df["profit"].tolist()
                    + forecast_df["profit"].round().tolist()
                ],
                betweenes_index=int(historical_df["doc"].max()),
                labels=[["origin", "predicted"]],
                legend=False,
                base_color="#474DA4",
                forecast_color="#FBBC05",
            ).plot()

            production_forecast = {
                "title": "Production Forecast",
                "data": [
                    {
                        "title": Constant.TITLE_CURRENT_BIOMASS,
                        "value": historical_df["biomass_kg"].iloc[-1],
                        "unit": "kg",
                        "description": Constant.CURRENT_BIOMASS_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_FORECASTED_BIOMASS,
                        "value": (
                            round(forecast_df["harvest_biomass_kg"].iloc[-1])
                            if forecast_df.shape[0] > 0
                            else 0
                        ),
                        "unit": "kg",
                        "description": Constant.FORECASTED_BIOMASS_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_CURRENT_ABW,
                        "value": historical_df["abw"].iloc[-1],
                        "unit": "gr",
                        "description": Constant.CURRENT_ABW_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_FORECASTED_ABW,
                        "value": (
                            round(forecast_df["adj_abw"].iloc[-1], 2)
                            if forecast_df.shape[0] > 0
                            else 0
                        ),
                        "unit": "gr",
                        "description": Constant.FORECASTED_ABW_DESCRIPTION,
                    },
                ],
                "plot": {
                    "forecast_biomass": forecast_biomass,
                    "forecast_abw": forecast_abw,
                },
            }

            economic_forecast = {
                "title": Constant.TITLE_ECONOMIC_FORECAST,
                "data": [
                    {
                        "title": Constant.TITLE_CURRENT_REVENUE,
                        "value": f"{historical_df['cum_realized_revenue'].iloc[-1]:,}",
                        "unit": "Rp",
                        "description": Constant.CURRENT_REVENUE_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_FORECASTED_REVENUE,
                        "value": (
                            f"{forecast_df['cum_realized_revenue'].iloc[-1].round():,}"
                            if forecast_df.shape[0] > 0
                            else "0"
                        ),
                        "unit": "Rp",
                        "description": Constant.FORECASTED_REVENUE_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_CURRENT_PROFIT,
                        "value": f"{historical_df['profit'].iloc[-1]:,}",
                        "unit": "Rp",
                        "description": Constant.CURRENT_PROFIT_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_FORECASTED_PROFIT,
                        "value": (
                            f"{forecast_df['profit'].iloc[-1].round():,}"
                            if forecast_df.shape[0] > 0
                            else "0"
                        ),
                        "unit": "Rp",
                        "description": Constant.FORECASTED_PROFIT_DESCRIPTION,
                    },
                ],
                "plot": {
                    "forecast_revenue": forecast_revenue,
                    "forecast_profit": forecast_profit,
                },
            }

            feeding_forecast = {
                "title": "Feeding Forecast",
                "data": [
                    {
                        "title": "DOC",
                        "value": max_doc,
                        "unit": "days",
                        "description": "",
                    },
                    {
                        "title": Constant.TITLE_CURRENT_FCR,
                        "value": round(historical_df["fcr"].iloc[-1], 2),
                        "unit": "",
                        "description": Constant.CURRENT_FCR_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_FORECASTED_FCR,
                        "value": round(forecast_df["fcr"].iloc[-1], 2),
                        "unit": "",
                        "description": Constant.FORECASTED_FCR_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_FEED_GIVEN_CURRENT,
                        "value": round(historical_df["cum_feed"].iloc[-1], 2),
                        "unit": "kg",
                        "description": Constant.CURRENT_FEED_GIVEN_DESCRIPTION,
                    },
                    {
                        "title": Constant.TITLE_FEED_GIVEN_FORECASTED,
                        "value": round(forecast_df["cum_feed"].iloc[-1], 2),
                        "unit": "kg",
                        "description": Constant.FORECASTED_FEED_GIVEN_DESCRIPTION,
                    },
                ],
            }

        except (AttributeError, KeyError, ValueError, IndexError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Load forecasted data successfully",
            payload={
                "feeding_forecast": feeding_forecast,
                "production_forecast": production_forecast,
                "economic_forecast": economic_forecast,
            },
        )

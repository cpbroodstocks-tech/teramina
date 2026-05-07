import copy
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline, interp1d

# from .weight.weight_kalman import WeightKalman
from .weight.weight_adg import Growth
from .biomass.biomass_formula_based_adg import Biomass

from ..helpers.constant_value import Constant
from ..helpers.utils import combinate


class Optimization:
    """Optimization service"""

    def __init__(
        self, historical_df: pd.DataFrame, forecast_df: pd.DataFrame, **kwargs
    ):
        """Optimization service

        Args:
            historical_df (pd.DataFrame): historical farming data
            forecast_df (pd.DataFrame): forecasted farming data
            kwargs: keyword arguments
                growth_config (dict): growth's parameters
                population_config (dict): population's parameters
                cost_config (dict): cost's parameters
                temperature_fr_array (np.ndarray): array of temperature data for FR
                price_array (np.ndarray): array of shrimp price based on the size
                required_columns (list): required columns
                is_ph_as_biomass (bool, optional): ph values condition. Defaults to False.
        """

        # unpack keywords arguments
        growth_config = kwargs.get("growth_config")
        population_config = kwargs.get("population_config")
        cost_config = kwargs.get("cost_config")
        temperature_fr_array = kwargs.get("temperature_fr_array")
        price_array = kwargs.get("price_array")
        required_columns = kwargs.get("required_columns")

        self.historical_population_config = copy.deepcopy(population_config)
        self.price_array = price_array
        self.cost_config = cost_config
        self.historical_population = historical_df["population"].to_numpy()

        # temperature data is list that contains temperature data for fr
        # and the daily temperature data
        self.temperature_data = [
            temperature_fr_array,
            np.append(
                historical_df[required_columns[0]].values,
                forecast_df[required_columns[0]].values,
            ),
        ]

        forecast_population_config = copy.deepcopy(population_config)
        forecast_population_config["initial_stocking"] = historical_df[
            "population"
        ].iloc[-1]
        forecast_population_config["doc_final"] = Constant.MAX_DOC

        forecast_wt, population = self.__generate_forecast_population(
            forecast_df=forecast_df,
            forecast_growth_config=copy.deepcopy(growth_config),
            forecast_population_config=forecast_population_config,
            historical_growth_config=copy.deepcopy(growth_config),
            historical_population_config=copy.deepcopy(population_config),
            required_columns=required_columns,
            forecast_w0=historical_df[required_columns[-1]].iloc[-1],
            # alpha=historical_df[["alpha1", "alpha2", "alpha3", "alpha4"]].iloc[-1],
        )

        self.combined_wt = np.append(
            historical_df[required_columns[-1]].values, forecast_wt
        )
        self.forecast_population = population

    def __generate_forecast_population(self, **kwargs):
        """_summary_

        Args:
            kwargs: Keyword Arguments
                forecast_df (pd.DataFrame):
                forecast_growth_config
                forecast_population_config
                historical_growth_config
                historical_population_config
                required_columns (list):
                forecast_w0 (float):
                alpha (list):
        """
        forecast_df = kwargs.get("forecast_df")
        forecast_growth_config = kwargs.get("forecast_growth_config")
        forecast_population_config = kwargs.get("forecast_population_config")
        historical_growth_config = kwargs.get("historical_growth_config")
        historical_population_config = kwargs.get("historical_population_config")
        required_columns = kwargs.get("required_columns")
        forecast_w0 = kwargs.get("forecast_w0")
        # alpha = kwargs.get("alpha")

        # forecast_growth = WeightKalman(
        #     df=forecast_df,
        #     t=forecast_population_config["doc_final"],
        #     conditions=[
        #         historical_growth_config["temp_condition"],
        #         historical_growth_config["do_condition"],
        #         historical_growth_config["nh3_condition"],
        #     ],
        #     required_columns=required_columns,
        #     t0=historical_population_config["doc_final"],
        #     w0=forecast_w0,
        #     wn=historical_growth_config["wn"],
        # )

        forecast_growth = Growth(
            df=forecast_df,
            t=forecast_population_config["doc_final"],
            conditions=[
                historical_growth_config["temp_condition"],
                historical_growth_config["do_condition"],
                historical_growth_config["nh3_condition"],
            ],
            required_columns=required_columns,
            t0=historical_population_config["doc_final"],
            w0=forecast_w0,
            wn=historical_growth_config["wn"],
        )

        forecast_wt = forecast_growth.wt()
        # forecast_wt = np.zeros(forecast_growth.t - forecast_growth.t0)

        # for idx, day in enumerate(range(forecast_growth.t - forecast_growth.t0)):
        # forecast_wt[idx] = forecast_growth.calculate_weight(
        #     alpha=alpha,
        #     t=day,
        #     t0=day - 1,
        #     w0=forecast_growth.w0 if idx == 0 else forecast_wt[idx - 1],
        #     wn=forecast_growth.wn,
        # )

        forecasting = Biomass(
            t0=historical_population_config["doc_final"],
            t=forecast_population_config["doc_final"],
            population_config=forecast_population_config,
            growth_config=forecast_growth_config,
            df=forecast_df,
            required_columns=required_columns,
            is_docfinal_similar_with_last=False,
            is_forecast=True,
            wt_forecast=forecast_wt,
            is_ph_as_biomass=False,
            use_filtering=True,
        )
        return forecast_wt, forecasting.get_population_values()

    def __set_price_function(self):
        price_data = np.append([[0, 0]], self.price_array, axis=0)
        f_price = CubicSpline(price_data[:, 0], price_data[:, 1])
        return f_price

    def generate_required_matrices(self, max_doc=Constant.MAX_DOC):
        """generate required matrices"""
        docfinal = self.historical_population_config["doc_final"]
        total_observation = max_doc - docfinal
        if total_observation > 60:
            # generate the harvested combination matrix
            t_harvest = combinate(
                60,
                Constant.MAX_PARTIAL_HARVEST
                - len(self.historical_population_config["ph"]),
            )

            # combined with forecasted data that under doc 60
            t_harvest = np.concatenate(
                (np.zeros((t_harvest.shape[0], total_observation - 60)), t_harvest),
                axis=1,
            )
        else:
            # set total forecasted data that will be observed tobe zero
            # means there is no any actions when doc < 60
            achieved = False
            while not achieved:
                try:
                    t_harvest = combinate(
                        total_observation,
                        Constant.MAX_PARTIAL_HARVEST
                        - len(self.historical_population_config["ph"]),
                    )

                    achieved = True
                except IndexError:
                    t_harvest = combinate(total_observation, total_observation)
                    achieved = True

        # define population of forecasted matrix
        # genearate matrix forecast population based on t_harvest
        # print(t_harvest.shape, self.forecast_population)
        matrix_forecast_population = np.full_like(t_harvest, self.forecast_population)
        # generate the percentage value and then multiply it with forecast population
        matrix_forecast_ph = (
            matrix_forecast_population * np.random.rand(*t_harvest.shape) * t_harvest
        )
        cumsum_matrix_forecast_ph = np.cumsum(matrix_forecast_ph, axis=1)

        historical_ph = np.zeros(docfinal)
        if self.historical_population_config["partial_doc"]:
            historical_ph[
                np.array(self.historical_population_config["partial_doc"]) - 1
            ] = self.historical_population_config["ph"]

        matrix_population_combined = np.concatenate(
            (
                np.full((t_harvest.shape[0], docfinal), self.historical_population),
                matrix_forecast_population - cumsum_matrix_forecast_ph,
            ),
            axis=1,
        )
        matrix_population_combined[matrix_population_combined < 0] = 0

        matrix_ph = np.concatenate(
            (
                np.full((t_harvest.shape[0], docfinal), historical_ph),
                matrix_forecast_ph,
            ),
            axis=1,
        )
        matrix_ph[matrix_population_combined == 0] = 0

        matrix_wt = np.tile(self.combined_wt, (t_harvest.shape[0], 1))

        # get matrix biomass
        matrix_biomass = (matrix_wt * matrix_population_combined) / 1000

        # get matrix harvested biomass
        matrix_harvested_biomass = (matrix_ph * matrix_wt) / 1000

        return (
            matrix_wt,
            matrix_population_combined,
            matrix_biomass,
            matrix_harvested_biomass,
            matrix_ph,
            total_observation,
            t_harvest.shape[0],  # total of combination data
        )

    def generate_revenue(self, matrix_wt, matrix_harvested_biomass):
        """generate revenue

        Args:
            matrix_wt (np.ndarray): array of weight values
            matrix_harvested_biomass (np.ndarray): array of harvested biomass
        """
        f_price = self.__set_price_function()

        #  size
        matrix_size = 1000 / matrix_wt

        # get matrix price
        matrix_price = f_price(matrix_size)

        # revenue
        matrix_revenue = matrix_harvested_biomass * matrix_price
        return matrix_revenue

    def __get_temp_extrapolation_func(self):
        """generate extrapolation function for temperature data"""
        data = self.temperature_data[0]
        f_15_19 = interp1d(data[:, 0], data[:, 1], fill_value="extrapolate")
        f_19_21 = interp1d(data[:, 0], data[:, 2], fill_value="extrapolate")
        f_21_24 = interp1d(data[:, 0], data[:, 3], fill_value="extrapolate")
        f_24_28 = interp1d(data[:, 0], data[:, 4], fill_value="extrapolate")
        f_28_32 = interp1d(data[:, 0], data[:, 5], fill_value="extrapolate")
        f_33 = interp1d(data[:, 0], data[:, 6], fill_value="extrapolate")
        f_34 = interp1d(data[:, 0], data[:, 7], fill_value="extrapolate")

        return f_15_19, f_19_21, f_21_24, f_24_28, f_28_32, f_33, f_34

    def __adjusted_fr_by_temp(self, f, blind_fr, abw, temperature):
        ranges = [(15, 19), (19, 21), (21, 24), (24, 28), (28, 32), (32, 33), (33, 34)]
        for i, func in enumerate(f):
            condition = (temperature >= ranges[i][0]) & (temperature < ranges[i][1])
            blind_fr[condition] = func(abw[condition])
        return blind_fr / 100

    def __generate_fr(self, total_observation, total_combination, matrix_wt):
        """

        Returns:
            tuple: tuple of
                matrix fr based on temperature
                matrix of doc's value
        """
        docfinal = self.historical_population_config["doc_final"]
        length_cycle = docfinal + total_observation

        # get doc
        doc = np.arange(length_cycle) + 1
        matrix_doc = np.full((total_combination, length_cycle), doc)

        # get temp fr
        f = self.__get_temp_extrapolation_func()
        temp_array = self.__adjusted_fr_by_temp(
            f,
            np.zeros(self.temperature_data[1].shape),
            matrix_wt[0],
            self.temperature_data[1],
        )

        matrix_temp_fr = np.full((total_combination, length_cycle), temp_array)
        return matrix_temp_fr, matrix_doc

    def generate_cost(
        self,
        matrix_temp_fr: np.ndarray,
        matrix_harvested_biomass: np.ndarray,
        matrix_biomass: np.ndarray,
        **kwargs
    ):
        """generate daily cost data

        Args:
            matrix_temp_fr (np.ndarray): matrix fr based on temperature
            matrix_harvested_biomass (np.ndarray): matrix of harvested biomass
            matrix_biomass (np.ndarray): matrix of biomass
            kwargs : keyword arguments
                total_observation (int):
                total_combination (int):
                observed_data (int):

        Returns:
            np.ndarray: matrix of daily cost data
        """

        total_combination = kwargs.get("total_combination")
        length_cycle = self.historical_population_config["doc_final"] + kwargs.get(
            "total_observation"
        )

        # total energy cost
        matrix_energy = np.tile(
            np.ones(length_cycle) * np.mean(self.cost_config["energy_cost"]) * 820 * 24,
            (total_combination, 1),
        )

        # total probiotics cost
        matrix_probiotics = np.tile(
            np.ones(length_cycle) * np.mean(self.cost_config["probiotics_cost"]),
            (total_combination, 1),
        )

        # total labor cost
        matrix_labor = np.tile(
            np.ones(length_cycle) * np.mean(self.cost_config["labor_cost"]),
            (total_combination, 1),
        )

        # total bonus
        matrix_bonus = matrix_harvested_biomass * np.mean(self.cost_config["bonus"])

        # total harvest
        matrix_harvest_cost = matrix_harvested_biomass * np.mean(
            self.cost_config["harvest_cost"]
        )

        # total feed cost
        matrix_feed_cost = (
            matrix_temp_fr * matrix_biomass * np.mean(self.cost_config["feed_cost"])
        )

        # total other cost
        matrix_other = np.tile(
            np.ones(length_cycle) * np.mean(self.cost_config["other"]),
            (total_combination, 1),
        )

        # total daily cost
        matrix_day_cost = (
            matrix_energy
            + matrix_probiotics
            + matrix_labor
            + matrix_bonus
            + matrix_harvest_cost
            + matrix_feed_cost
            + matrix_other
        )

        return matrix_day_cost

    def get_optimal_harvest(self):
        """generate optimal harvest values

        Return
            tuple : tuple of list amount of partial harvest and the related DOC
        """
        (
            matrix_wt,
            _,
            matrix_biomass,
            matrix_harvested_biomass,
            matrix_ph,
            total_observation,
            total_combination,
        ) = self.generate_required_matrices()

        matrix_revenue = self.generate_revenue(matrix_wt, matrix_harvested_biomass)
        matrix_temp_fr, matrix_doc = self.__generate_fr(
            total_observation, total_combination, matrix_wt
        )
        daily_cost = self.generate_cost(
            matrix_temp_fr,
            matrix_harvested_biomass,
            matrix_biomass,
            total_observation=total_observation,
            total_combination=total_combination,
        )

        # Get index of max profit
        max_index = np.argmax(np.sum(matrix_revenue - daily_cost, axis=1))

        # Get the PH and related amounts for the row with max profit
        selected_ph = matrix_ph[max_index]

        return selected_ph[selected_ph != 0], matrix_doc[max_index, selected_ph != 0]

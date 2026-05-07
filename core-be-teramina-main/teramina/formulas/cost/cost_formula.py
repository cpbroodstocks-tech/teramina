# pylint: disable=E0401
import pandas as pd
import numpy as np

from teramina.formulas.feed.feed_formula import Feed
from teramina.helpers.constant_value import Constant


class Cost(Feed):
    """Cost services"""

    def __init__(self, df: pd.DataFrame, wt_forecast: list = None, **kwargs):
        """Cost services

        Args:
            df (pd.DataFrame): farming data
            wt_forecast (list, optional): list of forecasted weight values. Defaults to None.
            **kwargs: keyword arguments
                t (int): time t
                t0 (int): initial time
                required_columns (list): list of required columns
                cost_config (dict): cost's parameters
                population_config (dict): population's paramaters
                growth_config (dict): growth's parameters
                is_docfinal_similar_with_last (bool):
                                    flag condition for doc final match the last data
                is_forecast (bool): flag condition wether forecast or not
                is_ph_as_biomass (bool):
                                    flag condition for partial harvest type of data
                is_final_harvest_defined (bool):
                                    flag condition wether final harvest occure or not
                trays (pd.DataFrame): tray leftover dataframe
                feed_temp_data (pd.DataFrame): feed temperature dataframe
                protein_content (float): protein content value
        """
        required_columns = kwargs.get("required_columns", ["Temp", "DO", "NH3", "ABW"])
        cost_config = kwargs.get("cost_config")

        super().__init__(
            population_config=kwargs.get("population_config"),
            growth_config=kwargs.get("growth_config"),
            df=df,
            wt_forecast=wt_forecast,
            t=kwargs.get("t"),
            t0=kwargs.get("t0"),
            required_columns=required_columns,
            is_docfinal_similar_with_last=kwargs.get("is_docfinal_similar_with_last"),
            is_forecast=kwargs.get("is_forecast"),
            is_ph_as_biomass=kwargs.get("is_ph_as_biomass"),
            is_final_harvest_defined=kwargs.get("is_final_harvest_defined"),
            trays=kwargs.get("trays"),
            feed_temp_data=kwargs.get("feed_temp_data"),
            protein_content=kwargs.get("protein_content"),
        )

        self.cost_items = cost_config
        self.is_forecast = kwargs.get("is_forecast")

    def daily_cost(self):
        """generate daily cost data. It's contains harvest, energy, probiotics & feed cost"""

        if self.is_forecast:
            # harvest cost
            harvest_biomass = self.get_harvest_biomass_values() / 1000
            harvest_cost = harvest_biomass * np.mean(self.cost_items["harvest_cost"])

            # feed cost
            fr = self.get_current_fr()[0]
            biomass = self.get_biomass_values() / 1000
            feed_cost = biomass * fr * np.mean(self.cost_items["feed_cost"])

            # energy cost
            energy_cost = np.mean(self.cost_items["energy_cost"]) * Constant.AERATOR_WATTS * Constant.HOURS_PER_DAY
            energy_cost = np.full_like(harvest_cost, energy_cost)

            # probiotic cost
            probiotics_cost = np.mean(self.cost_items["probiotics_cost"])
            probiotics_cost = np.full_like(harvest_cost, probiotics_cost)

            other_cost = np.zeros_like(harvest_cost)
            labor_cost = np.zeros_like(harvest_cost)
            bonus_cost = np.zeros_like(harvest_cost)
        else:
            other_cost = self.cost_items["other"]
            labor_cost = self.cost_items["labor_cost"]
            energy_cost = self.cost_items["energy_cost"] * Constant.AERATOR_WATTS * Constant.HOURS_PER_DAY
            bonus_cost = self.cost_items["bonus"]
            harvest_cost = self.cost_items["harvest_cost"]
            probiotics_cost = self.cost_items["probiotics_cost"]
            feed_cost = self.cost_items["feed_cost"]

        max_doc = self.doc_final if self.is_docfinal_similar_with_last else self.t
        energy_cost[max_doc:] = 0
        probiotics_cost[max_doc:] = 0
        other_cost[max_doc:] = 0
        labor_cost[max_doc:] = 0

        cost_array = np.array(
            [
                harvest_cost,
                energy_cost,
                probiotics_cost,
                other_cost,
                labor_cost,
                bonus_cost,
                feed_cost,
            ]
        )

        if "seed_cost" in self.cost_items.keys():
            pl_cost = np.zeros_like(harvest_cost)
            if not self.is_forecast:
                pl_cost = self.cost_items["seed_cost"]

            cost_array = np.append(cost_array, [pl_cost], axis=0)

        cost_array = cost_array[:, : self.t - self.t0]

        return cost_array

    def cost_per_kg(self):
        """generate cost per kg value"""
        total_cost = np.cumsum(self.daily_cost().sum(axis=0))
        cost_per_kg = total_cost / (self.get_total_biomass_values() / 1000)
        return cost_per_kg

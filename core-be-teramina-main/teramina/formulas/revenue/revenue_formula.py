# pylint: disable=R0801

import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
from teramina.formulas.biomass.biomass_formula_based_adg import Biomass


class Revenue(Biomass):
    """revenue service"""

    def __init__(
        self,
        population_config: dict,
        growth_config: dict,
        df: pd.DataFrame,
        wt_forecast=None,
        **kwargs
    ):
        """Revenue Service

        Args:
            population_config (dict): population's parameters
            growth_config (dict): growth's parameter
            df (pd.DataFrame): farming data
            wt_forecast (list, optional): list of forecasted weight values. Defaults to None.
            kwargs : keyword arguments
                t (int): time t
                t0 (int): initial time
                required_columns (list): list of required columns
                is_docfinal_similar_with_last (bool):
                                    flag condition for doc final match the last data
                is_forecast (bool): flag condition wether forecast or not
                is_ph_as_biomass (bool):
                                    flag condition for partial harvest type of data
                is_final_harvest_defined (bool):
                                    flag condition wether final harvest occure or not
                price_array (np.ndarray): array of price data
        """
        # unpack keywords arguments
        t = kwargs.get("t")
        t0 = kwargs.get("t0")
        required_columns = kwargs.get("required_columns", ["Temp", "DO", "NH3", "ABW"])
        is_docfinal_similar_with_last = kwargs.get(
            "is_docfinal_similar_with_last", True
        )
        is_forecast = kwargs.get("is_forecast", False)
        is_ph_as_biomass = kwargs.get("is_ph_as_biomass", False)
        is_final_harvest_defined = kwargs.get("is_final_harvest_defined", False)
        price_array = kwargs.get("price_array")

        super().__init__(
            population_config=population_config,
            growth_config=growth_config,
            df=df,
            wt_forecast=wt_forecast,
            t=t,
            t0=t0,
            required_columns=required_columns,
            is_docfinal_similar_with_last=is_docfinal_similar_with_last,
            is_forecast=is_forecast,
            is_ph_as_biomass=is_ph_as_biomass,
            is_final_harvest_defined=is_final_harvest_defined,
            use_filtering=True,
        )

        price_data = np.append([[0, 0]], price_array, axis=0)
        self.f_price = CubicSpline(price_data[:, 0], price_data[:, 1])

    def realized_revenue(self) -> list:
        """generate realized revenue data"""
        harvest_biomas = self.get_harvest_biomass_values() / 1000  # convert to kg
        try:
            price_per_harvest = np.apply_along_axis(self.f_price, 0, 1000 / self.weight)
            price_per_harvest = np.where(
                (1000 / self.weight > 200) | (1000 / self.weight < 0),
                0,
                price_per_harvest,
            )
        except ValueError:
            price_per_harvest = 0
        real_revenue = harvest_biomas * price_per_harvest
        return real_revenue

    def potential_revenue(self) -> list:
        """generate potential revenue data"""
        wt = self.weight
        biomass = self.get_biomass_values() / 1000
        potential_revenue = np.zeros(self.t - self.t0)
        try:
            price = np.apply_along_axis(self.f_price, 0, 1000 / self.weight)
        except ValueError:
            price = np.zeros_like(wt)

        potential_revenue = np.heaviside(price, 1) * biomass * price

        return potential_revenue

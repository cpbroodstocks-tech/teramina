# pylint: disable=R0801, R0902

import numpy as np
import pandas as pd

from teramina.formulas.population.population_formula_based_adg import Population


class Biomass(Population):
    """Biomass service that leads to generate population and biomass data"""

    def __init__(
        self,
        population_config: dict,
        growth_config: dict,
        df: pd.DataFrame,
        wt_forecast: list = None,
        **kwargs
    ):
        """Biomass services

        Args:
            population_config (dict): _description_
            growth_config (dict): _description_
            df (pd.DataFrame): _description_
            wt_forecast (list, optional): _description_. Defaults to None.
            kwargs : keywords arguments

        Keyword Arguments
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
            use_filtering (bool):
                                flag condition wether used filtering or not
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
        use_filtering = kwargs.get("use_filtering", False)

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
            use_filtering=use_filtering,
        )

    def get_biomass_values(self) -> np.ndarray:
        """get array of biomass values

        Returns:
            (np.ndarray): array of biomass values (gram)
        """
        bt = self.get_population_values() * self.weight
        return bt

    def get_harvest_biomass_values(self) -> np.ndarray:
        """get array of harvested biomass values

        Returns:
            (np.ndarray): array of harvested biomass values (gram)
        """
        hbio = self.get_harvest_population_values() * self.weight
        return hbio

    def get_total_biomass_values(self) -> np.ndarray:
        """get array of total biomass values

        Returns:
            (np.ndarray): array of harvested total biomass values (gram)
        """
        total = self.get_biomass_values() + np.cumsum(self.get_harvest_biomass_values())
        return total

    def get_carriying_capacity_values(self, area, depth) -> np.ndarray:
        """generate carriying capacity

        Args:
            area (float): pond area (m^2)
            depth (float): pond depth (m)

        Returns
            (np.ndarray): array of carriying capacity (kg/m^3)
        """
        return self.get_biomass_values() / 1000 / (area * depth)

# pylint: disable=R0801, R0902, E0401, R0913
"""poputioon formula based on adg
this population not using kalman filter
"""

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from teramina.helpers.utils import heaviside_step
from teramina.formulas.weight.weight_adg import Growth


class Population(Growth):
    """Biomass service that leads to generate population and biomass data"""

    def __init__(
        self,
        population_config: dict,
        growth_config: dict,
        df: pd.DataFrame,
        wt_forecast: list = None,
        **kwargs,
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
        self.t = kwargs.get("t")
        self.t0 = kwargs.get("t0")
        required_columns = kwargs.get("required_columns", ["Temp", "DO", "NH3", "ABW"])
        is_docfinal_similar_with_last = kwargs.get(
            "is_docfinal_similar_with_last", True
        )
        is_forecast = kwargs.get("is_forecast", False)
        is_ph_as_biomass = kwargs.get("is_ph_as_biomass", False)
        is_final_harvest_defined = kwargs.get("is_final_harvest_defined", False)

        super().__init__(
            df=df,
            t=self.t,
            conditions=[
                growth_config["temp_condition"],
                growth_config["do_condition"],
                growth_config["nh3_condition"],
            ],
            required_columns=required_columns,
            t0=self.t0,
            w0=growth_config["w0"],
            wn=growth_config["wn"],
        )

        self.partial_doc = np.array(population_config["partial_doc"])
        self.doc_final = population_config["doc_final"]
        self.ph = np.array(population_config["ph"])

        self.population_parameter = [
            population_config["initial_stocking"],
            population_config["gamma"],
            population_config["nh3_limit"],
            -np.log(population_config["sr"]) / self.t,
            is_final_harvest_defined,
        ]

        self.is_docfinal_similar_with_last = is_docfinal_similar_with_last

        # set survival rate
        self.__set_survival_rate_data(df)

        if is_forecast:
            self.__initialize_forecast_data(wt_forecast)
        else:
            self.weight = self.wt()

        if is_ph_as_biomass and (self.ph.shape[0] != 0):
            # ph * 1000 is the converter to be gram
            self.ph = (self.ph * 1000) / (self.weight[self.partial_doc - self.t0 - 1])

    def __initialize_forecast_data(self, wt_forecast):
        self.weight = wt_forecast

        # adjustment
        current_index = np.where(self.partial_doc >= self.t0)[0]
        self.partial_doc = self.partial_doc[current_index]
        self.ph = self.ph[current_index]

        self.base_data[:, 3] = wt_forecast

    def __get_selected_data(self, df: pd.DataFrame) -> pd.DataFrame:
        temporary_df = df.iloc[self.t0 : self.t]
        if temporary_df.shape[0] == 0 or self.t > df.shape[0]:
            df = df.iloc[: self.t - self.t0].copy()
        else:
            df = temporary_df.copy()

        return df

    def __set_survival_rate_data(self, df: pd.DataFrame):
        ndf = self.__get_selected_data(df)
        try:
            # preprocess sr value
            ndf["sr"].interpolate(method="linear", inplace=True)
        except KeyError:
            ndf["sr"].fillna(1, inplace=True)

        # define the mortality rate
        doc = ndf["doc"].values

        try:
            self.survival_rate = CubicSpline(doc, ndf["sr"].values)
        except ValueError:
            self.survival_rate = CubicSpline([doc[0] - 1, doc[0]], np.ones(2) * 1)

    def __get_selected_partial_harvest(self, t) -> np.ndarray:
        partial_harvest_at_t = self.ph * heaviside_step(t - self.partial_doc)
        return partial_harvest_at_t

    def __calculate_total_population_at_t(self, t) -> float:
        result = self.population_parameter[0] * self.survival_rate(t)
        return result

    def __calculate_population_at_t(self, t) -> float:
        partial_harvest_at_t = self.__get_selected_partial_harvest(t)
        result = self.__calculate_total_population_at_t(t) - partial_harvest_at_t.sum()
        return result

    def __calculate_harvest_at_t(self, t) -> float:
        partial_harvest_at_t = self.__get_selected_partial_harvest(t)
        index_partial = np.where(self.partial_doc == t)[0].tolist()
        partial_harvest_at_t = (
            partial_harvest_at_t[index_partial] if index_partial else 0
        )

        if (
            (not self.population_parameter[4])
            and (self.doc_final not in self.partial_doc)
            and (t == self.doc_final)
            and self.is_docfinal_similar_with_last
        ):
            nt = self.__calculate_population_at_t(t)
            return partial_harvest_at_t + nt

        return partial_harvest_at_t

    def __calculate_remaining_pop_at_t(self, t):
        partial_harvest_at_t = self.ph * heaviside_step(t - self.partial_doc)
        return partial_harvest_at_t.sum()

    def get_population_values(self) -> list:
        """get list of population"""
        pops = np.zeros(self.t - self.t0)
        doc = np.arange(self.t0, self.t) + 1
        for i, j in enumerate(doc):
            if (j == self.doc_final) and self.is_docfinal_similar_with_last:
                pops[i] = 0
            else:
                pops[i] = self.__calculate_population_at_t(j)

        return pops

    def get_harvest_population_values(self) -> list:
        """get list of harvested population"""
        doc = np.arange(self.t0, self.t) + 1
        hpop = np.fromiter((self.__calculate_harvest_at_t(j) for j in doc), dtype=float)
        return hpop

    def get_remaining_population_values(self):
        """get list of remains population"""
        doc = np.arange(self.t0, self.t) + 1
        pops = np.fromiter(
            (self.__calculate_remaining_pop_at_t(j) for j in doc), dtype=float
        )
        return pops

    def get_total_population_values(self) -> list:
        """get total population"""
        pops = self.get_population_values() + np.cumsum(
            self.get_harvest_population_values()
        )
        return pops

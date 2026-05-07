# pylint: disable=R0801, E0401

import pandas as pd
import numpy as np

from teramina.formulas.biomass.biomass_formula_based_adg import Biomass
from teramina.helpers.constant_value import Constant

from teramina.formulas.feed.fr_main_formula import (
    FrByDPI,
    FrByBlindFeed,
    FrByTemperature,
    FrByTray,
    FrByDO,
    FrByNH3,
)


class Feed(Biomass):
    """Feed Services"""

    def __init__(
        self,
        population_config: dict,
        growth_config: dict,
        df: pd.DataFrame,
        wt_forecast: list = None,
        **kwargs
    ):
        """Feed Services

        Args:
            population_config (dict): population config
            growth_config (dict): growth config
            df (pd.DataFrame): farming data
            wt_forecast (list, optional): forecasted weight values. Defaults to None.
            kwargs : keyword arguments

        Keyword Arguments:
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
            trays (pd.DataFrame): tray leftover dataframe
            feed_temp_data (pd.DataFrame): feed temperature dataframe
            protein_content (float): protein content value
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

        self.feed_temp_data = kwargs.get("feed_temp_data")
        self.protein_content = kwargs.get("protein_content")
        self.trays = kwargs.get("trays")

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

        self.df = df

    def __init_fr(self) -> list:
        fr = FrByDPI().get_fr_by_dpi(self.protein_content, self.weight)[0]
        return fr

    def __blind_fr(self) -> list:
        population = self.get_total_population_values()
        biomass = self.get_total_biomass_values() / 1000

        fr = self.__init_fr()
        for i in np.arange(self.t - self.t0):
            if i <= Constant.EARLY_STAGE_DOC_THRESHOLD:
                fr[i] = FrByBlindFeed().blind_feed_nagrofa(i, population[i], biomass[i])

        return fr

    def __temp_fr(self) -> list:
        blind_fr = self.__blind_fr()
        weight_data = self.weight.reshape([self.weight.shape[0], 1])

        data = np.append(self.base_data, weight_data, axis=1)
        data = np.append(data, blind_fr.reshape([blind_fr.shape[0], 1]), axis=1)
        data = np.nan_to_num(data)

        blind_feed_data = data[np.where(data[:, 5] < 2)]
        data = data[np.where(data[:, 5] >= 2)]

        fr = FrByTemperature(self.feed_temp_data).adjusted_fr_by_temp_as_list(
            data[:, 5], data[:, 4]
        )
        fr = np.append(blind_feed_data[:, 6], fr)
        return fr

    def __do_fr(self) -> np.ndarray:
        fr = self.__temp_fr()
        do = self.df["do"].to_numpy()
        fr = FrByDO.get_list_adjusted_fr(do, fr)
        return fr

    def __nh3_fr(self) -> np.ndarray:
        fr = self.__do_fr()
        nh3 = self.df["nh3"].to_numpy()
        fr = FrByNH3.get_list_adjusted_fr(nh3, fr)
        return fr

    def __tray_fr(self) -> list:
        fr = self.__nh3_fr()
        periodic_fr = np.array(fr).reshape((len(fr), 1)) * [0.3, 0.2, 0.1, 0.4]
        fr, periodic_fr = FrByTray(self.trays).adjusted_by_periodic_fr(periodic_fr)
        return [fr, periodic_fr]

    def get_current_fr(self):
        """generate current feed ration"""
        try:
            if self.trays.empty:
                fr = self.__nh3_fr()
                periodic_fr = np.array(fr).reshape((len(fr), 1)) * [0.3, 0.2, 0.1, 0.4]
                return [fr, periodic_fr]

            return self.__tray_fr()
        except AttributeError:
            fr = self.__nh3_fr()
            periodic_fr = np.array(fr).reshape((len(fr), 1)) * [0.3, 0.2, 0.1, 0.4]
            return [fr, periodic_fr]

    def get_next_partial_feed_ration(self):
        """get value for next partial feed ration"""
        try:
            if self.trays.empty:
                return self.__temp_fr() / Constant.MAX_FEED_TIME

            return self.__tray_fr()[1]
        except AttributeError:
            return self.__temp_fr() / Constant.MAX_FEED_TIME

    def get_initial_fr(self):
        """generate feed ration based on initial condition"""
        return self.__init_fr()

    def get_blind_fr(self):
        """generate feed ration based on blind feed condition"""
        return self.__blind_fr()

    def get_temp_fr(self):
        """generate feed ration based on temperature condition"""
        return self.__temp_fr()

    def get_feed_given(self):
        """generate feed given based on all condition"""
        feed_given = self.get_current_fr()[0] * self.get_biomass_values() / 1000
        return feed_given

    def get_feed_given_at_init(self):
        """generate feed given based on initial condition"""
        feed_given = self.get_initial_fr() * self.get_biomass_values() / 1000
        return feed_given

    def get_feed_given_at_blind(self):
        """generate feed given based on blind feed condition"""
        feed_given = self.get_blind_fr() * self.get_biomass_values() / 1000
        return feed_given

    def get_feed_given_at_temp(self):
        """generate feed given based on temperature condition"""
        feed_given = self.get_temp_fr() * self.get_biomass_values() / 1000
        return feed_given

    def get_fcr(self):
        """generate FCR after all conditions"""
        total_biomass = self.get_total_biomass_values() / 1000
        cum_feed = np.cumsum(self.get_feed_given())
        fcr = cum_feed / total_biomass
        return fcr

    def get_fcr_at_init(self):
        """generate FCR based on initial condition"""
        total_biomass = self.get_total_biomass_values() / 1000
        cum_feed = np.cumsum(self.get_feed_given_at_init())
        fcr = cum_feed / total_biomass
        return fcr

    def get_fcr_at_blind(self):
        """generate FCR based on blind feed condition"""
        total_biomass = self.get_total_biomass_values() / 1000
        cum_feed = np.cumsum(self.get_feed_given_at_blind())
        fcr = cum_feed / total_biomass
        return fcr

    def get_fcr_at_temp(self):
        """generate FCR based on temperature condition"""
        total_biomass = self.get_total_biomass_values() / 1000
        cum_feed = np.cumsum(self.get_feed_given_at_temp())
        fcr = cum_feed / total_biomass
        return fcr

# pylint: disable=too-few-public-methods, E0401

import copy
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from teramina.helpers.utils import left_trapezoidal, normal_trapezoidal
from teramina.helpers.constant_value import Constant

MAX_FEED_TIME = 4
FEED_TIME_PERCENTAGE = np.array([0.3, 0.2, 0.1, 0.4])
TOTAL_TRAY = 7
TRAY_PERCENTAGE = np.array([0.14, 0.2, 0.16, 0.05, 0, 0.05, 0.1])


def generate_random_array(max_sum, max_length):
    """generate random array data

    Args:
        max_sum (float): maximum expected sum value
        max_length (float): maximum expected length value
    """
    # create an array of random values between 0 and 1
    values = np.random.rand(max_length)
    # scale the values to have a sum of max_sum
    values = values * (max_sum / np.sum(values))
    # round the values to the nearest integer
    # values = np.round(values).astype(int)
    # adjust the last value to ensure that the sum is exactly max_sum
    values[-1] += max_sum - np.sum(values)
    # shuffle the array to make it more random
    values = np.random.shuffle(values)
    return values


class FrByDPI:
    """Feed Ration Based on DPI"""

    @staticmethod
    def get_fr_by_dpi(protein_content: float, abw: list) -> tuple:
        """get fr by DPI

        Args:
            protein_content (float): protein content in that include in the feed
            abw (list): list of average body weight value
        """
        abw = np.array(abw)
        if 30 <= protein_content < 39:
            dpi = 44.7 * abw ** (-0.714)
        elif 39 <= protein_content <= 40:
            dpi = 53.64 * abw ** (-0.714)
        else:
            raise ValueError("Sorry, the protein content is not in range")

        fr = 1 / (protein_content / 100) * dpi / 1000

        return fr, dpi


class FrByBlindFeed:
    """Feed Ration Based on Blind Feed Condition"""

    @staticmethod
    def blind_feed_nagrofa(doc: int, population: float, biomass: float) -> float:
        """

        Args
            doc: daily of culture
            population: population at t
            biomass: biomass at t (kg)
        """
        if doc > 30:
            raise ValueError("Maximal blind feeding is at DOC's 30")

        current_feed_amount = population / 100000
        if 0 <= doc <= 10:
            doc = doc + 1 if doc == 0 else doc
            feed_per_day = current_feed_amount * (1 + (200 / 1000) * doc)
        elif 10 < doc <= 20:
            feed_rate = 1 + (200 / 1000) * 10 + (400 / 1000) * (doc - 10)
            feed_per_day = current_feed_amount * feed_rate
        else:
            feed_rate = 1 + ((200 + 400) / 1000) * 10 + (600 / 1000) * (doc - 20)
            feed_per_day = current_feed_amount * feed_rate

        fr = feed_per_day / biomass if biomass != 0 else 0

        return fr

    @staticmethod
    def adjust_fr_blind_feeding(
        doc: int, fr: float, population: float, biomass: float
    ) -> float:
        """

        Args:
            doc: daily of culture
            fr: feed ration
            population: population at t
            biomass: biomass at t (kg)
        """
        if fr > 30:
            return fr

        current_feed_amount = population / 100000
        if 0 <= doc <= 10:
            doc = doc + 1 if doc == 0 else doc
            feed_per_day = current_feed_amount * (1 + (200 / 1000) * doc)
        elif 10 < doc <= 20:
            feed_rate = 1 + (200 / 1000) * 10 + (400 / 1000) * (doc - 10)
            feed_per_day = current_feed_amount * feed_rate
        else:
            feed_rate = 1 + ((200 + 400) / 1000) * 10 + (600 / 1000) * (doc - 20)
            feed_per_day = current_feed_amount * feed_rate

        fr = feed_per_day / biomass

        return fr


class FrByTemperature:
    """Feed Ration Based on Temperature Data"""

    def __init__(self, df: pd.DataFrame, col_name_abw: str = "ABW"):
        """Feed ration based on temperature data

        Args:
            df (pd.DataFrame): farming data
            col_name_abw (str, optional): average body weight columns. Defaults to "ABW".
        """
        f_15_19 = interp1d(df[col_name_abw], df["15-19"], fill_value="extrapolate")
        f_19_21 = interp1d(df[col_name_abw], df["19-21"], fill_value="extrapolate")
        f_21_24 = interp1d(df[col_name_abw], df["21-24"], fill_value="extrapolate")
        f_24_28 = interp1d(df[col_name_abw], df["24-28"], fill_value="extrapolate")
        f_28_32 = interp1d(df[col_name_abw], df["28-32"], fill_value="extrapolate")
        f_33 = interp1d(df[col_name_abw], df["33"], fill_value="extrapolate")
        f_34 = interp1d(df[col_name_abw], df["34"], fill_value="extrapolate")

        self.interpolate_functions = [
            f_15_19,
            f_19_21,
            f_21_24,
            f_24_28,
            f_28_32,
            f_33,
            f_34,
        ]

    def adjusted_fr_by_temp(self, abw: float, temperature: float) -> float:
        """generate adjusted fr by temperature

        Args:
            abw (float): average body weight's value
            temperature (float): temperature's value

        Return
            float : feed ration value
        """
        funcs = {
            (15, 19): self.interpolate_functions[0],
            (19, 21): self.interpolate_functions[1],
            (21, 24): self.interpolate_functions[2],
            (24, 28): self.interpolate_functions[3],
            (28, 32): self.interpolate_functions[4],
            (32, 33): self.interpolate_functions[5],
            (33, 34): self.interpolate_functions[6],
        }
        for (min_temp, max_temp), func in funcs.items():
            if min_temp <= temperature < max_temp:
                new_fr = func(abw)
                return new_fr / 100

        return 0

    def adjusted_fr_by_temp_as_list(self, abw: list, temp: list) -> list:
        """adjusted fr by temperature

        Args:
            abw (list): list of average body weight
            temp (list): list of current temperature
        """
        fr = [float(self.adjusted_fr_by_temp(abw[i], j)) for i, j in enumerate(temp)]
        return fr


class FrByDO:
    """Feed Ration Based on DO data"""

    @staticmethod
    def adjusted_do(do_value):
        """generate adjusted DO

        Args:
            do_value (float): DO's value
        """
        adj_do = normal_trapezoidal(
            do_value,
            suitable_min=Constant.DO_SUITABLE_MIN,
            suitable_max=Constant.DO_SUITABLE_MAX,
            optimal_min=Constant.DO_OPTIMAL_MIN,
            optimal_max=Constant.DO_OPTIMAL_MAX,
        )

        return adj_do

    @staticmethod
    def adjusted_fr_by_do(do_value, fr):
        """generate adjusted fr by DO

        Args:
            do_value (float): current DO's value
            fr (float): current FR's value
        """
        adj_do = FrByDO.adjusted_do(do_value)
        return adj_do * fr

    @staticmethod
    def get_list_adjusted_fr(do: np.ndarray, fr: np.ndarray):
        """generate adjusted fr by DO as list

        Args
            do (np.ndarray): array of current DO's value
            fr (np.ndarray): array of current FR's value
        """
        adj_do = [FrByDO.adjusted_do(i) for i in do]
        new_fr = np.array(adj_do[: len(fr)]) * fr
        return new_fr


class FrByNH3:
    """Feed Ration Based on NH3 Data"""

    @staticmethod
    def adjusted_nh3(nh3_value):
        """generate adjusted NH3 value

        Args:
            nh3_value (float): NH3's value
        """
        adj_nh3 = left_trapezoidal(
            nh3_value,
            suitable_min=Constant.NH3_SUITABLE_MIN,
            suitable_max=Constant.NH3_SUITABLE_MAX,
            optimal_max=Constant.NH3_OPTIMAL_MAX,
        )
        return adj_nh3

    @staticmethod
    def adjusted_fr_by_nh3(nh3_value, fr):
        """generate fr adjusted NH3

        Args:
            nh3_value (float): current nh3's value
            fr (float): current feed ration's value
        """
        adj_nh3 = FrByNH3.adjusted_nh3(nh3_value)
        return adj_nh3 * fr

    @staticmethod
    def get_list_adjusted_fr(nh3: np.ndarray, fr: np.ndarray):
        """generate fr adjusted NH3

        Args:
            nh3 (np.ndarray): array of nh3's values
            fr (np.ndarray): array of current fr's values
        """
        adj_nh3 = [FrByNH3.adjusted_nh3(i) for i in nh3]
        new_fr = np.array(adj_nh3[: len(fr)]) * fr
        return new_fr


class FrByTray:
    """Feed Ration Based on Tray's Leftover"""

    def __init__(self, tray: pd.DataFrame) -> None:
        """
        Args:
            tray (pd.DataFrame): dataframe that contains tray data
        """
        self.tray = tray.values

    def __get_feed_point(self, excess_percent: float) -> int:
        """feed point per tray

        Args:
            excess_percent (float): excess percentation / leftover percentation
        """

        if excess_percent == 0:
            point = 3
        elif excess_percent <= 10:
            point = 1
        else:
            point = 0

        return point

    def __feed_point_generator(self, excess_percent: float) -> float:
        if excess_percent == 0:
            point = 3
        elif excess_percent <= 10:
            point = -excess_percent / 5 + 3
        else:
            point = -excess_percent / 90 + 10 / 9

        return point

    def adjusted_fr_by_leftover(
        self, fr: float, tray_excess: list, is_excess_aggregate=False
    ) -> float:
        """generate fr adjusted by leftover

        Args:
            fr (float): current feed ration
            tray_excess (list): list of excess percentation in trays
            is_excess_aggregate (bool): True when excess aggregated in
                    a single day not for each trays separately. Default False.
        """
        if not is_excess_aggregate:
            feed_points = sum(self.__get_feed_point(i) for i in tray_excess)
            if feed_points >= 15:
                adjusted_point = 10
            elif 11 <= feed_points < 15:
                adjusted_point = 5
            elif 6 <= feed_points < 11:
                adjusted_point = 0
            elif 4 <= feed_points < 6:
                adjusted_point = -5
            else:
                adjusted_point = -10
        else:
            feed_points = sum(self.__feed_point_generator(i) for i in tray_excess)
            adjusted_point = 20 / 3 * feed_points - 10

        return fr * (1 + adjusted_point / 100)

    def adjusted_fr_per_day(self, fr: list) -> list:
        """generate fr adjusted per day

        Args:
            fr (list): list of feed ration in each day

        Return:
            list : list of adjusted fr in each day
        """
        fr = copy.deepcopy(fr)
        doc = np.unique(self.tray[:, 0]).astype(int)  # get column DOC
        next_feed_ration = np.array(fr) / MAX_FEED_TIME

        for t in doc:
            index = np.where(self.tray[:, 0] == t)
            selected_data = self.tray[index]
            current_amount_partial = selected_data.shape[0]
            periodic_fr = fr[t - 1] * FEED_TIME_PERCENTAGE

            for i in range(current_amount_partial):
                if i != MAX_FEED_TIME - 1:
                    adjusted_next_feed_ration = self.adjusted_fr_by_leftover(
                        periodic_fr[i + 1], selected_data[i, 1:], True
                    )
                    periodic_fr[i + 1] = adjusted_next_feed_ration

            fr[t - 1] = periodic_fr.sum()
            next_feed_ration[t - 1] = copy.deepcopy(adjusted_next_feed_ration)

        return [fr, next_feed_ration]

    def adjusted_by_periodic_fr(self, periodic_fr: np.ndarray):
        """generate periodic fr

        Args:
            periodic_fr (np.ndarray): Array of periodic fr in each day
        """
        max_feed_time = periodic_fr.shape[1]
        doc = np.unique(self.tray[:, 0]).astype(int)  # get column DOC

        for t in doc:
            index = np.where(self.tray[:, 0] == t)
            selected_data = self.tray[index]
            current_amount_partial = selected_data.shape[0]
            current_periodic_fr = periodic_fr[t - 1]

            for i in range(current_amount_partial):
                if i != max_feed_time - 1:
                    adjusted_next_feed_ration = self.adjusted_fr_by_leftover(
                        current_periodic_fr[i + 1], selected_data[i, 1:], True
                    )
                    current_periodic_fr[i + 1] = adjusted_next_feed_ration

            periodic_fr[t - 1] = current_periodic_fr

        fr = np.sum(periodic_fr, axis=1)
        return fr, periodic_fr

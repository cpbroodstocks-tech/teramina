# pylint: disable=too-many-arguments, E0401, R0801, too-many-positional-arguments

import numpy as np
import pandas as pd

from scipy.optimize import curve_fit
from scipy.interpolate import CubicSpline
from scipy.integrate import quad

from teramina.helpers.utils import normal_trapezoidal, left_trapezoidal

####
# the order of data base
# 0: adjusted temperature
# 1: DO
# 2: NH3
# 3: init ABW
# 4: origin temperature
# 5: adjusted ABW
# 6: fr
# 7: doc
####

BASE_TEMPERATURE_DATA = np.loadtxt(
    "teramina/helpers/data_example/base_temperature_data.csv", delimiter=","
)


class Growth:
    """Individual growth service"""

    def __init__(
        self,
        df: pd.DataFrame,
        t: int,
        conditions: list,
        required_columns=None,
        **kwargs,
    ) -> None:
        """Growth service

        Args:
            df (pd.DataFrame): _description_
            t (int): _description_
            conditions (list): data conditions. It's contains
                    temperature, do, and nh3 condition
            required_columns (list, optional): list of requiered columns.
                    Defaults to None.
            kwargs : keyword arguments
                t0 (int): initial t
                w0 (float): initial weight
                wn (float): expected weight
        """
        if required_columns is None:
            required_columns = ["Temp", "DO", "NH3", "ABW"]

        self.t0 = kwargs.get("t0", 1)
        self.w0 = kwargs.get("w0", df[required_columns[3]].iloc[0])
        self.wn = kwargs.get("wn", 45)
        self.t = t

        # set conditions instances with conditions contains
        # temp_condition, do_condition, nh3_condition
        self.conditions = conditions
        self.base_data = self.__data_prep(self.t0, t, required_columns, df)

    def __data_prep(self, t0, t, required_columns, df: pd.DataFrame):
        _, _, _, abw_column = required_columns

        # check to make sure the availablity of ABW
        if df.shape[0] != (df["doc"].iloc[-1] - df["doc"].iloc[0] + 1):
            df = self.__complete_data(df)
        temporary_df = df.iloc[t0:t]
        if temporary_df.shape[0] == 0 or t > df.shape[0]:
            df = df.iloc[: t - t0].copy()
        else:
            df = df.iloc[t0:t].copy()

        if abw_column not in df.columns:
            df.loc[:, abw_column] = np.nan

        # initialize data
        base_data = df[required_columns].values

        # temperature data adjustment
        f_temp_criteria = CubicSpline(
            BASE_TEMPERATURE_DATA[:, 0], BASE_TEMPERATURE_DATA[:, 1]
        )

        base_data[:, 0] = np.nan_to_num(
            base_data[:, 0], nan=np.nanmean(base_data[:, 0])
        )
        base_data[:, 0] = np.apply_along_axis(f_temp_criteria, 0, base_data[:, 0])

        # do data adjustment
        do_condition = self.conditions[1]
        normal_trapezoidal_func = np.vectorize(
            lambda x: normal_trapezoidal(
                x, do_condition[0], do_condition[3], do_condition[1], do_condition[2]
            )
        )
        base_data[:, 1] = normal_trapezoidal_func(base_data[:, 1])

        # nh3 data adjustment
        nh3_condition = self.conditions[2]
        left_trapezoidal_func = np.vectorize(
            lambda x: left_trapezoidal(
                x, nh3_condition[0], nh3_condition[3], nh3_condition[2]
            )
        )
        base_data[:, 2] = left_trapezoidal_func(base_data[:, 2])

        try:
            nan_check = np.isnan(base_data[:, 3])
        except TypeError:
            nan_check = list(base_data[:, 3])
            nan_check = np.isnan(nan_check)

        if any(nan_check):
            base_data = self.__impute_abw(base_data)

            # adjust by the curve fit parameter
            base_data = self.__impute_abw(base_data)

        # add origin temperature
        array_temp = df[required_columns[0]].values
        base_data = np.append(
            base_data, array_temp.reshape([array_temp.shape[0], 1]), axis=1
        )

        return base_data

    def __complete_data(self, df: pd.DataFrame):
        n = df["doc"].iloc[-1]
        complete_df = pd.DataFrame({"doc": range(1, n + 1)})
        merged_df = complete_df.merge(df, on="doc", how="left")
        return merged_df

    def __impute_abw(self, base_data: np.ndarray):
        # set initial value
        if np.sum(~np.isnan(base_data[:, 3])) > 1:
            nan_indices = np.isnan(base_data[:, 3])
            non_nan_indices = np.arange(len(base_data[:, 3]))[~nan_indices]
            base_data[:, 3][nan_indices] = np.interp(
                np.where(nan_indices)[0],
                non_nan_indices,
                base_data[:, 3][~nan_indices],
            )
        else:
            alpha1, alpha2, alpha3, alpha4 = (
                0.06383328,
                0.00581553,
                0.00164433,
                0.00019466,
            )

            wt = self.wt(base_data, alpha1, alpha2, alpha3, alpha4)

            # get nan indices
            origin_wt = base_data[:, 3]
            nan_indices = np.isnan(origin_wt)
            origin_wt[nan_indices] = wt[nan_indices]
            base_data[:, 3] = origin_wt

        return base_data

    def wt(
        self,
        data: np.ndarray,
        alpha1: float,
        alpha2: float,
        alpha3: float,
        alpha4: float,
    ):
        """basic weight function

        Args:
            data (np.ndarray): base data
            alpha1 (float): multiplier for integral of temperature
            alpha2 (float): multiplier for integral of do
            alpha3 (float): multiplier for integral of nh3
            alpha4 (float): multiplier for integral of t

        Returns:
            np.ndarray: array of weight values
        """
        # alpha1, alpha2, alpha3, alpha4 = args
        n = self.t - self.t0
        weight = np.zeros(n)

        wn_cubed = self.wn ** (1 / 3)
        w0_cubed = self.w0 ** (1 / 3)

        integrals = {}
        for i in range(n):
            if i == 0:
                integrals[i] = (data[:, 0][i], data[:, 1][i], data[:, 2][i], self.t0)
            else:
                if i - 1 in integrals:
                    last_integrals = integrals[i - 1]
                else:
                    last_integrals = (
                        np.trapz(data[:, 0][:i]),
                        np.trapz(data[:, 1][:i]),
                        np.trapz(data[:, 2][:i]),
                        quad(lambda x: 1, self.t0, self.t0 + i - 1)[0],
                    )
                    integrals[i - 1] = last_integrals
                integrals[i] = (
                    last_integrals[0] + data[:, 0][i],
                    last_integrals[1] + data[:, 1][i],
                    last_integrals[2] + data[:, 2][i],
                    last_integrals[3] + i,
                )

            value = (
                wn_cubed
                - (wn_cubed - w0_cubed)
                * np.exp(
                    -1
                    * (
                        alpha1 * integrals[i][0]
                        + alpha2 * integrals[i][1]
                        + alpha3 * integrals[i][2]
                        + alpha4 * integrals[i][3]
                    )
                )
            ) ** 3

            if (value < weight[i - 1]) & (i != 0):
                weight[i] = weight[i - 1].copy()
            else:
                weight[i] = value

        return weight

    def fit(self):
        """OLS functions to find alphas"""
        alpha = curve_fit(self.wt, self.base_data, self.base_data[:, 3], bounds=(-1, 1))
        return alpha[0]

    def mse(self, alpha):
        """Mean squared error for data that used specific alpha"""
        alpha, alpha1, alpha2, alpha3 = alpha
        weight = np.asarray(self.wt(self.base_data, alpha, alpha1, alpha2, alpha3))
        data = (self.base_data[:, 3] - weight) ** 2
        return np.mean(data)

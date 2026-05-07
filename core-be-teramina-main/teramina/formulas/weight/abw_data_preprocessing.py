# pylint: disable=R0801,E0401
"""it is helpers functions"""

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from teramina.helpers.utils import normal_trapezoidal, left_trapezoidal
from teramina.formulas.weight.simple_weight import wt

BASE_TEMPERATURE_DATA = np.loadtxt(
    "teramina/helpers/data_example/base_temperature_data.csv", delimiter=","
)


def abw_data_prep(t0, t, required_columns, df: pd.DataFrame, conditions: list):
    """function to preprocess the data in each growth service initialization.

    Args:
        t0 (int): initial t
        t (int): max doc
        df (pd.DataFrame): dataframe of farming data
        required_columns (list, optional): list of requiered columns.
        conditions (list): list of conditions from temperature, nh3, and do
    """
    abw_column = required_columns[-1]

    # check to make sure the availablity of ABW
    if df.shape[0] != (df["doc"].iloc[-1] - df["doc"].iloc[0] + 1):
        df = complete_data(df)

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

    base_data[:, 0] = np.nan_to_num(base_data[:, 0], nan=np.nanmean(base_data[:, 0]))
    base_data[:, 0] = np.apply_along_axis(f_temp_criteria, 0, base_data[:, 0])

    # do data adjustment
    do_condition = conditions[1]
    normal_trapezoidal_func = np.vectorize(
        lambda x: normal_trapezoidal(
            x, do_condition[0], do_condition[3], do_condition[1], do_condition[2]
        )
    )
    base_data[:, 1] = normal_trapezoidal_func(base_data[:, 1])

    # nh3 data adjustment
    nh3_condition = conditions[2]
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
        # adjust by the curve fit parameter
        base_data = impute_abw(base_data)

    # add origin temperature
    array_temp = df[required_columns[0]].values
    base_data = np.append(
        base_data, array_temp.reshape([array_temp.shape[0], 1]), axis=1
    )

    return base_data


def complete_data(df: pd.DataFrame):
    """completing the data if the doc none"""
    n = df["doc"].iloc[-1]
    complete_df = pd.DataFrame({"doc": range(1, n + 1)})
    merged_df = complete_df.merge(df, on="doc", how="left")
    return merged_df


def impute_abw(base_data: np.ndarray):
    """impute abw"""
    # if there are at least two weight data, it will be impute using interpolation
    # Assuming base_data is a 2D NumPy array
    column_3 = list(base_data[:, 3])
    # Check for NaN values using boolean indexing
    non_nan_indices = ~np.isnan(column_3)
    if np.sum(non_nan_indices) > 1:
        nan_indices = np.isnan(base_data[:, 3])
        non_nan_indices = np.arange(len(base_data[:, 3]))[~nan_indices]
        base_data[:, 3][nan_indices] = np.interp(
            np.where(nan_indices)[0],
            non_nan_indices,
            base_data[:, 3][~nan_indices],
        )
        return base_data

    # set initial value using simple wt based on adg
    # w[t+1] = w[t] + adg
    base_data[:, 3] = np.array(wt(1, len(base_data[:, 3]) + 1))
    return base_data

# pylint: disable=E0402, missing-function-docstring, missing-class-docstring, too-few-public-methods

import pandas as pd
import numpy as np

# from scipy.interpolate import CubicSpline

from ...helpers.constant_value import Constant


class ForecastData:
    @staticmethod
    def get_forecast_df(historical_df: pd.DataFrame):
        historical_docfinal = historical_df["doc"].iloc[-1]
        total_observation = Constant.MAX_DOC - int(historical_docfinal)

        sr_values = historical_df["sr"].values
        mask = np.isnan(sr_values)
        # Find the index of the last False value in the mask (last non-NaN value)
        last_non_nan_index = np.where(~mask)[0][-1]

        # Get the last non-NaN value
        sr_value = sr_values[last_non_nan_index]

        # sr_values = np.where(np.equal(sr_values, None), 1, sr_values)
        # sr_values = np.nan_to_num(sr_values, nan=1)
        # sr_func = CubicSpline(historical_df["doc"].values, sr_values)
        # sr = sr_func(doc)
        doc = np.arange(
            historical_docfinal + 1, historical_docfinal + total_observation + 1
        )

        historical_df = historical_df[["do", "temperature", "nh3"]]
        mean_values = np.full((total_observation, 3), historical_df.mean().values)
        forecast_df = pd.DataFrame(mean_values, columns=historical_df.columns)
        forecast_df["doc"] = doc
        forecast_df["sr"] = sr_value

        return {
            "historical_docfinal": historical_docfinal,
            "forecast_total_observation": total_observation,
            "table": forecast_df.set_index(np.arange(total_observation)),
        }

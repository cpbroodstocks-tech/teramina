# pylint: disable=unsubscriptable-object
import pandas as pd
import numpy as np

# from teramina.data_generator.forecast.forecast_data_generator import (
#     ForecastDataGenerator,
# )
from teramina.data_generator.forecast.forecast_data_based_adg import (
    ForecastDataGenerator,
)
from teramina.formulas.sgr.growth_rate import Sgr


class CombinedDataGenerator(ForecastDataGenerator):
    """Data generator which related to the historical and forecasted data"""

    def __init__(self, cycle_id):
        self.cycle_id = cycle_id

        super().__init__(cycle_id)

    def set_combined_data(
        self, historical_df: pd.DataFrame, forecated_df: pd.DataFrame = None
    ) -> pd.DataFrame:
        """combining historical and forecasted farm data

        Args:
            historical_df (pd.DataFrame): historical farm data
            forecated_df (pd.DataFrame): forecasted farm data.
                    But could be None when there is no forecasted data

        Returns:
            pd.DataFrame: combined data
        """

        if isinstance(forecated_df, pd.DataFrame):
            # add category to each table
            historical_df.loc[:, "category"] = "historical"
            forecated_df.loc[:, "category"] = "forecast"

            # combined each table to single table
            df = pd.concat([historical_df, forecated_df], ignore_index=True)
        else:
            historical_df.loc[:, "category"] = "historical"
            df = historical_df.copy()

        # add cum feed given into the combined dataframe
        df["cum_feed"] = np.cumsum(df["feed_given"])
        df["cum_feed"] = df["cum_feed"].astype(float)
        # add fcr into the combined dataframe
        df.eval("fcr = cum_feed / total_biomass", inplace=True)
        # add cum total cost into the combined dataframe
        df["cum_total_cost"] = np.cumsum(df["total_cost"])
        # add cost per kg into the combined dataframe
        df.eval("cost_per_kg = cum_total_cost / total_biomass", inplace=True)
        # add cum realized revenue into the combined dataframe
        df["cum_realized_revenue"] = np.cumsum(df["realized_revenue"])
        # add profit into the combined dataframe
        df["profit"] = np.cumsum(df.eval("realized_revenue - total_cost"))
        # add potential profit into the combined dataframe
        df["potential_profit"] = (
            df["profit"] + df["potential_revenue"] - df["total_cost"].cumsum()
        )
        # add date into the combined dataframe
        df["date"] = pd.date_range(
            start=df["date"].loc[0], periods=df.shape[0], freq="D"
        )

        df["sgr"] = Sgr(df["abw"].tolist()).calculate()

        return df

    def generate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """combined data generator

        Args:
            df (pd.DataFrame): origin data

        Returns:
            pd.DataFrame: processed data
        """
        df1 = self.generate_historical_result(df, False)
        if (df1["doc"].iloc[-1] <= 30) or (df1["doc"].iloc[-1] == 120):
            df2 = None
        else:
            df2 = self.generate_forecast_result(df1, use_harvest_recommendation=True)

        res = self.set_combined_data(df1, df2)
        return res

# pylint: disable=E0401, W0613
import numpy as np
import pandas as pd

from teramina.formulas.revenue.revenue_formula import Revenue
from teramina.formulas.cost.cost_formula import Cost


def set_revenue_data(df: pd.DataFrame, revenue_object: Revenue, is_forecast=False):
    """get & set revenue data to dataframe"""
    df["adj_abw"] = revenue_object.weight
    df["population"] = revenue_object.get_population_values()
    df["biomass_kg"] = revenue_object.get_biomass_values() / 1000
    df["harvest_biomass_kg"] = revenue_object.get_harvest_biomass_values() / 1000
    df["harvest_population"] = revenue_object.get_harvest_population_values()
    df["total_biomass"] = revenue_object.get_total_biomass_values() / 1000
    df["realized_revenue"] = revenue_object.realized_revenue()
    df["potential_revenue"] = revenue_object.potential_revenue()


    # if not is_forecast:
    #     alpha = revenue_object.alphas
    #     df[["alpha1", "alpha2", "alpha3", "alpha4"]] = alpha

    return df


def set_cost_data(df: pd.DataFrame, cost_object: Cost):
    """get & set cost data to dataframe"""

    columns_data = df.columns

    # triggering to call count daily cost data and the related
    cost_array = cost_object.daily_cost()
    cost_array = np.nan_to_num(cost_array, nan=0)

    if len(cost_array) >= 7:
        df["cost_harvest"] = np.nan_to_num(cost_array[0], nan=0)
        df["cost_energy"] = np.nan_to_num(cost_array[1], nan=0)
        df["cost_probiotics"] = np.nan_to_num(cost_array[2], nan=0)
        df["cost_other"] = np.nan_to_num(cost_array[3], nan=0)
        df["cost_labor"] = np.nan_to_num(cost_array[4], nan=0)
        df["cost_bonuss"] = np.nan_to_num(cost_array[5], nan=0)
        df["cost_feed"] = np.nan_to_num(cost_array[6], nan=0)

        if len(cost_array) == 8:
            df["cost_seed"] = np.nan_to_num(cost_array[7], nan=0)

    df["total_cost"] = cost_array.sum(axis=0).astype("float")

    adj_fr, adj_periodic_fr = cost_object.get_current_fr()
    df["adj_fr"] = np.array(adj_fr).astype(float)

    periodic_df = pd.DataFrame(adj_periodic_fr)
    periodic_df.columns = [
        "feed_ration_1",
        "feed_ration_2",
        "feed_ration_3",
        "feed_ration_4",
    ]
    df = pd.concat([df, periodic_df], axis=1)

    df["fcr"] = cost_object.get_fcr()
    df["cost_per_kg"] = cost_object.cost_per_kg()
    df["initial_fr"] = cost_object.get_initial_fr()

    if "feed_given" in columns_data:
        df["feed_given"] = df["feed_given"].fillna(0)
        df["realized_fcr"] = np.cumsum(df["feed_given"]) / df["total_biomass"]
    else:
        df["feed_given"] = cost_object.get_feed_given()

    if "realized_fcr" not in df.columns:
        if "fr" in columns_data:
            df["realized_fcr"] = np.cumsum(
                df.eval("(fr / 100) / (biomass_kg / total_biomass)")
            )
        else:
            df["realized_fcr"] = np.cumsum(
                df.eval("adj_fr * biomass_kg / total_biomass")
            )

    return df

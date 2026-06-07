import pandas as pd

from teramina.helpers.constant_column import Column
from teramina.helpers.constant_value import Constant


def parse_harvest_data(doc_data, harvest_data, final_doc, final_harvest, **kwargs):
    """General parse harvest data function"""

    if final_harvest not in (None, ""):
        harvest_data.append(final_harvest)
        doc_data.append(final_doc)
        is_final_harvest_defined = True
    else:
        is_final_harvest_defined = False

    partial_doc = [doc for doc in doc_data if doc not in ("", None)]
    partial_harvest = [harvest for harvest in harvest_data if harvest not in ("", None)]

    result = {
        "partial_harvest": partial_harvest,
        "partial_doc": partial_doc,
        "final_doc": final_doc,
        "final_harvest": final_harvest,
        "is_final_harvest_defined": is_final_harvest_defined,
    }

    revenue_data = kwargs.get("revenue_data", None)
    if revenue_data:
        final_revenue = kwargs.get("final_revenue", None)
        if final_harvest not in (None, ""):
            revenue_data.append(final_revenue)

        realized_revenue = [
            revenue for revenue in revenue_data if revenue not in ("", None)
        ]
        result["revenue"] = realized_revenue

    return result


def parse_harvest_data_input(data):
    """parse harvest data input format"""
    doc_data = [data[key]["doc"] for key in ["partial1", "partial2", "partial3"]]
    harvest_data = [
        data[key]["biomass"] for key in ["partial1", "partial2", "partial3"]
    ]
    revenue_data = [
        data[key]["revenue"] for key in ["partial1", "partial2", "partial3"]
    ]

    final_doc = data["final"]["doc"]
    final_harvest = data["final"]["biomass"]
    final_revenue = data["final"]["revenue"]

    return parse_harvest_data(
        doc_data,
        harvest_data,
        final_doc,
        final_harvest,
        revenue_data=revenue_data,
        final_revenue=final_revenue,
    )


def set_params_config(
    df: pd.DataFrame, ph: list, partial_doc: list, docfinal: int
) -> tuple:
    """setup the parameter configuration, including for growth, population, and cost.

    Args:
        df (pd.DataFrame): _description_
        ph (list): list of amount of partial harvest (in percent)
        partial_doc (list): list of daily culture of partial harvest
        docfinal (int): daily culture of final harvest

    Returns:
        tuple: there are init_data, population_config, growth_config, & cost_config
    """

    init_data = df[Column.single_data_columns].loc[0].copy()
    init_data["protein_content"] = df["protein_content"].iloc[-1]

    population_config = {
        "initial_stocking": init_data["initial_stocking"],
        "sr": init_data["sr"] if init_data["sr"] else 1,
        "ph": ph,
        "partial_doc": partial_doc,
        "doc_final": docfinal,
        "gamma": Constant.GAMMA,
        "nh3_limit": Constant.NH3_LIM,
    }

    growth_config = {
        "w0": init_data["w0"],
        "wn": Constant.WN,
        "temp_condition": [],
        "do_condition": [
            Constant.DO_SUITABLE_MIN,
            Constant.DO_OPTIMAL_MIN,
            Constant.DO_OPTIMAL_MAX,
            Constant.DO_SUITABLE_MAX,
        ],
        "nh3_condition": [
            Constant.NH3_SUITABLE_MIN,
            Constant.NH3_OPTIMAL_MIN,
            Constant.NH3_OPTIMAL_MAX,
            Constant.NH3_SUITABLE_MAX,
        ],
    }

    cost_config = {
        "harvest_cost": init_data["harvest_cost"],
        "energy_cost": init_data["energy_cost"],
        "probiotics_cost": init_data["probiotic_cost"],
        "labor_cost": df["labor_cost"].values,
        "bonus": df["bonus_cost"].values,
        "other": df["other_cost"].values,
        "feed_cost": init_data["feeding_cost"],
    }

    cost_config = {
        "harvest_cost": df["harvest_cost"].values,
        "energy_cost": df["energy_cost"].values,
        "probiotics_cost": df["probiotic_cost"].values,
        "labor_cost": df["labor_cost"].values,
        "bonus": df["bonus_cost"].values,
        "other": df["other_cost"].values,
        "feed_cost": df["feeding_cost"].values,
    }

    if "seed_cost" in df.columns:
        cost_config["seed_cost"] = df["seed_cost"].values

    return init_data, population_config, growth_config, cost_config

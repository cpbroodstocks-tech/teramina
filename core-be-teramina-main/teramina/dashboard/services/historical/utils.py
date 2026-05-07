# pylint: disable=E0401
import os
import re
import json
import pandas as pd
import requests

from teramina.cycle.models.cycle_model import Cycle
from teramina.pond.models.pond_model import Pond
from teramina.cycle_data.models.cycle_data_model import ResultData
from teramina.dashboard.services.dashboard_utils import get_max_filter_doc

CHAT_BASE_URL = os.getenv("CHAT_BASE_URL")

def get_result_dataframe(cycle_id, date) -> pd.DataFrame:
    """get the result data from the table ResultData in dataframe and filtered by t

    Returns:
        pd.DataFrame: dataframe of the result data
    """

    result = ResultData.objects(cycle_id=cycle_id).only("result_data").first()
    # check is it not empty
    if not result:
        raise ValueError(f"Data with cycle {cycle_id} doesn't exist")

    df = pd.DataFrame(result.result_data)
    t = get_max_filter_doc(cycle_id, False, date)
    df = df.iloc[:t]
    return df


def get_list_cycle_id(pond_id):
    """get list of cycle id"""
    cycles = Cycle.objects(pond_id=pond_id).only("id", "is_active").all()
    cycles = [str(i.id) for i in cycles if i.is_active is True]
    return cycles


def get_list_pond_id(farm_id):
    """get list of pond id"""
    ponds = Pond.objects(farm_id=farm_id).only("id").all()
    ponds = [str(i.id) for i in ponds]
    return ponds


def get_selected_data(farm_id, pond_id=None, cycle_id=None, date=None):
    """get selected data"""
    if cycle_id:
        df = get_result_dataframe(cycle_id, date)
        group_df = [df]
    elif pond_id:
        list_cycle_id = get_list_cycle_id(pond_id)
        group_df = []
        for cycle in list_cycle_id:
            df = get_result_dataframe(cycle, date)
            df.drop(["date", "category"], axis=1, inplace=True)
            group_df.append(df)

        if len(group_df) == 0:
            raise AttributeError("There is no active cycle")

        if len(group_df) > 1:
            grouper = pd.concat(group_df).groupby(level=0)
            df = grouper.sum()
            mean_group = grouper.mean()
            df["cost_per_kg"] = mean_group["cost_per_kg"]
        else:
            df = group_df[0]
    else:
        list_pond_id = get_list_pond_id(farm_id)
        group_df = []
        for pnd in list_pond_id:
            cycles = get_list_cycle_id(pnd)
            sub_group_df = []
            for cycle in cycles:
                df = get_result_dataframe(cycle, date)
                df.drop(["date", "category"], axis=1, inplace=True)
                sub_group_df.append(df)

            group_df += sub_group_df

        if len(group_df) == 0:
            raise AttributeError("There is no active cycle")

        if len(group_df) > 1:
            grouper = pd.concat(group_df).groupby(level=0)
            df = grouper.sum()
            mean_group = grouper.mean()
            df["cost_per_kg"] = mean_group["cost_per_kg"]
        else:
            df = group_df[0]

    return df, group_df

def extract_json(text):
    """extract_json"""
    # Use regular expressions to find the JSON string
    pattern = r"```json\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1)
        # Load the JSON string into a Python dictionary
        data = json.loads(json_str)
        return data

    return None


def ask_question(bearer_token, question):
    """ask question"""
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    # question = self.report_prompt(data_to_interprete)
    result = requests.post(
        f"{CHAT_BASE_URL}/v2/single-chat?question={question}",
        headers=headers,
        timeout=90,
    ).json()
    result = extract_json(result["output"])
    return result

import copy
import numpy as np

from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.data_generator.helpers.utils import parse_harvest_data


def generate_harvest_data(
    historical_ph, historical_partial_doc, forecast_ph, forecast_partial_doc
):
    """generate harvest daat"""
    ph_status = np.all(np.isnan(forecast_ph))
    partial_doc_status = np.all(np.isnan(forecast_partial_doc))

    if not ph_status and not partial_doc_status:
        ph = np.append(historical_ph, forecast_ph)
        partial_doc = np.append(historical_partial_doc, forecast_partial_doc)

    else:
        ph = copy.copy(historical_ph)
        partial_doc = copy.copy(historical_partial_doc)

    data = {}
    for idx, value in enumerate(zip(ph, partial_doc)):
        value_data = {"doc": int(value[1]), "biomass": float(value[0])}

        if idx != 3:
            data[f"partial{idx + 1}"] = value_data
        else:
            data["final"] = value_data

    return data


def parse_harvest_data_simulation(data: dict) -> dict:
    """parse harvest data simulation

    Args:
        data (dict): partial harvest data, with format like below
                    ```
                    {
                        "partial1": {
                            "doc": 60,
                            "biomass": 75
                        }
                    }
                    ```

    Returns:
        dict: contains information about partial_harvest (list), partial doc (list)
            final_doc (int), final_harvest (float), is_final_harvest_defined (bool)
    """
    doc_data = [data[f"partial{i}"]["doc"] for i in range(1, 4)]
    harvest_data = [data[f"partial{i}"]["biomass"] for i in range(1, 4)]

    final_doc = data["final"]["doc"]
    final_harvest = data["final"]["biomass"]
    return parse_harvest_data(doc_data, harvest_data, final_doc, final_harvest)


def update_harvest_recommendation_table(cycle_id, harvest_data):
    """updater for harvest recommendation table"""
    harvest_object = HarvestRecommendation.objects(cycle_id=cycle_id).first()
    if harvest_object:
        harvest_object.harvest_data = harvest_data
        harvest_object.save()
    else:
        HarvestRecommendation(cycle_id=cycle_id, harvest_data=harvest_data).save()

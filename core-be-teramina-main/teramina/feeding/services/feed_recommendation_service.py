from datetime import datetime
import pandas as pd
import numpy as np

from ...cycle_data.models.cycle_data_model import ResultData
from ...cycle.models.cycle_model import Cycle
from ...helpers.unit import Unit
from ...helpers.constant_value import Constant
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema


class FeedRecommendationService:
    """Feed Recommendation Service"""

    def __init__(self, cycle_id):
        self.cycle_id = cycle_id

    def __get_result_data(self):
        data = ResultData.objects(cycle_id=self.cycle_id).only("result_data").first()
        if not data:
            raise ValueError(
                "Sorry, no data yet. Something went wrong or it’s taking time."
            )

        df = pd.DataFrame(data.result_data)
        return df

    def __get_max_doc(self, df: pd.DataFrame, date: str) -> int:
        """Finding the maximal DOC

        Args:
            df (pd.Dataframe): Dataframe of data
            date (str): string of date with structure %m/%d/%Y

        Raises:
            LookupError: raised up when the cycle data with specified id doesn't found

        Returns:
            int: maximal DOC
        """

        max_data, _ = df.shape
        end_date = datetime.strptime(date, "%m/%d/%Y")
        end_date = datetime.now() if end_date > datetime.now() else end_date

        cycle = Cycle.objects(id=self.cycle_id).only("start_date").first()
        if not cycle:
            raise LookupError(f"cycle data with id {self.cycle_id} was not found")

        start_date = cycle.start_date
        doc = (end_date - start_date).days + 1

        doc = max_data if doc > max_data else doc
        return doc

    def __parse_recommendation_data(self, df: pd.DataFrame, doc: int) -> list:
        """parsing the recommendation data

        Args
            df (pd.Dataframe): dataframe
            doc (int): DOC

        Returns:
            list: list of recommendation data
        """

        if df.loc[doc - 1, "biomass_kg"] == 0:
            biomass = df.loc[doc - 1, "harvest_biomass_kg"]
        else:
            biomass = df.loc[doc - 1, "biomass_kg"]

        fr = df.loc[doc - 1, "adj_fr"]
        feed_given = fr * biomass
        row = df.loc[doc - 1]
        periodic_fr = np.array(
            [
                row.get(column, fr / 4)
                for column in [
                    "feed_ration_1",
                    "feed_ration_2",
                    "feed_ration_3",
                    "feed_ration_4",
                ]
            ],
            dtype=float,
        )
        periodic_fr = np.nan_to_num(periodic_fr, nan=fr / 4)
        periodic_feed_given = periodic_fr * biomass
        result_feed_given = np.append(feed_given, periodic_feed_given)

        result = []
        for i, j in enumerate(result_feed_given):
            title = "Feed Given" if i == 0 else f"Ration {i}"
            description = "" if i != 0 else Constant.FEEDING_RATION_DESCRIPTION
            result.append(
                {
                    "title": title,
                    "value": round(j, 2),
                    "unit": Unit.kg,
                    "description": description,
                }
            )

        return result

    def get_list_recommendation(self, date):
        """get list recommendation"""
        if not date:
            date = datetime.strftime(datetime.now(), "%m/%d/%Y")

        df = self.__get_result_data()
        max_doc = self.__get_max_doc(df, date)
        ration_recommender = self.__parse_recommendation_data(df, max_doc)
        return ration_recommender

    def get_recommendation(self, date: str = None):
        """get recommendation data"""
        try:
            ration_recommender = self.get_list_recommendation(date)
        except (ValueError, KeyError, IndexError, AttributeError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200, message="success", payload={"data": ration_recommender}
        )

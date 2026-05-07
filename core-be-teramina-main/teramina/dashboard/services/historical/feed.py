import pandas as pd
import numpy as np
from mongoengine.errors import InvalidQueryError

from teramina.feeding.services.feed_realization_service import FeedRealizationService
from teramina.feeding.services.feed_recommendation_service import (
    FeedRecommendationService,
)

from teramina.helpers.constant_value import Constant
from teramina.helpers.unit import Unit
from teramina.helpers.plot import Line
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from teramina.dashboard.services.historical.utils import get_result_dataframe


class DashboardFeed:
    """Dashboard Feed"""

    def __init__(self, farm_id, pond_id=None, cycle_id=None, date=None):
        self.farm_id = farm_id
        self.pond_id = pond_id
        self.cycle_id = cycle_id
        self.date = date

    def __generate_feeding_status_data(self, df: pd.DataFrame):
        feed_cost = df["cost_feed"].cumsum().iloc[-1].round()
        cum_feed = round(df["cum_feed"].iloc[-1], 2)

        feeding_status = {
            "title": Constant.TITLE_FEEDING_STATUS,
            "data": [
                {"title": "DOC", "value": int(df["doc"].max()), "unit": "days"},
                {
                    "title": Constant.TITLE_FEED_GIVEN,
                    "value": cum_feed,
                    "unit": Unit.kg,
                },
                {
                    "title": Constant.TITLE_FEED_COST,
                    "value": f"Rp {feed_cost:,}",
                    "unit": "",
                },
                {
                    "title": Constant.TITLE_FEED_CONVERTION_RATE,
                    "value": round(df["realized_fcr"].iloc[-1], 3),
                    "unit": "",
                },
                {
                    "title": Constant.TITLE_FEED_RATE,
                    "value": round(float(df["fr"].iloc[-1]), 2),
                    "unit": Unit.percent,
                },
            ],
        }

        return feeding_status

    def daily_feed_adjustment(self):
        """daily feed adjustment"""
        # feed realization data
        feed_realization_data = FeedRealizationService(
            self.cycle_id
        ).get_list_feed_data(self.date)[0]

        # feed recommendation
        feed_recommendation_data = FeedRecommendationService(
            self.cycle_id
        ).get_list_recommendation(self.date)

        return {
            "title": Constant.TITLE_DAILY_FEED_ADJUSTMENT,
            "data": [
                {"title": "Recommendation", "data": feed_recommendation_data},
                {"title": "Realization", "data": feed_realization_data},
            ],
        }

    def generate_feed_adjusment_metric(self, df: pd.DataFrame):
        """Generate feed adjusment metric"""
        try:
            chb = int(df["chb"].loc[0])
            cp = int(df["protein_content"].loc[0])
            gcd = np.gcd(chb, cp)
            chb = chb / gcd
            cp = cp / gcd
        except ValueError:
            chb = df["chb"].loc[0]
            cp = df["protein_content"].loc[0]

        feed_adjustment_data = [
            {
                "title": Constant.TITLE_ORIGINAL_FEEDING_RATE,
                "value": round(float(df["fr"].iloc[-1]), 2),
                "unit": Unit.percent,
                "description": Constant.ORIGINAL_FEEDING_RATE_DESCRIPTION,
            },
            {
                "title": Constant.TITLE_ADJUSTMENT_FEEDING_RATE,
                "value": round(df["adj_fr"].iloc[-1] * 100, 2),
                "unit": Unit.percent,
                "description": Constant.ADJUSTED_FEEDING_RATE_DESCRIPTION,
            },
            {
                "title": Constant.TITLE_PROTEIN_CONTENT,
                "value": float(df["protein_content"].iloc[-1]),
                "unit": Unit.percent,
                "description": Constant.PROTEIN_CONTENT_DESCRIPTION,
            },
            {
                "title": Constant.TITLE_CHB_CP,
                "value": f"{round(chb)}:{round(cp)}",
                "unit": "",
                "description": Constant.CHB_CP_DESCRIPTION,
            },
        ]

        return feed_adjustment_data

    def feed(self):
        """feed data"""
        try:
            if not self.cycle_id:
                raise AttributeError("Please select a cycle")

            df = get_result_dataframe(self.cycle_id, self.date)
            df["fr"] = df["fr"].replace(np.nan, 0)

            # generate the feeding status metric
            feeding_status = self.__generate_feeding_status_data(df)

            # generate feed plot
            feed_plot = Line(
                title="",
                x=df["doc"].tolist(),
                y=[(df["fr"] / 100).round(2).tolist(), df["adj_fr"].round(2).tolist()],
                labels=["original", "adjustment"],
                legend=True,
            ).plot()
            feed_plot["color"] = ["#474DA4", "#FBBC05"]

            # generate the feed adjustment metric
            feed_adjusment_data = self.generate_feed_adjusment_metric(df)
            feeding_adjustment = {
                "title": "Original Feeding Rate",
                "data": feed_adjusment_data,
                "plot": feed_plot,
            }

            # generate the daily feed adjustment
            daily_feeding_adjustment = self.daily_feed_adjustment()

        except (ValueError, KeyError, AttributeError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except LookupError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception), payload={})

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "feed_status": feeding_status,
                "feed_adjustment": feeding_adjustment,
                "daily_feed_adjustment": daily_feeding_adjustment,
            },
        )

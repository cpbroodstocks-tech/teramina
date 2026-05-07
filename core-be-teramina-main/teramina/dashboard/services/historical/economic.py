# pylint: disable=C0209,E0401
import pandas as pd
from mongoengine.errors import InvalidQueryError

from teramina.helpers.constant_column import Column
from teramina.helpers.constant_value import Constant
from teramina.helpers.unit import Unit
from teramina.helpers.plot import Pie, Line
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from teramina.dashboard.services.historical.utils import get_selected_data


class DashboardEconomic:
    """Dashboard Economic"""

    def __init__(self, farm_id, pond_id=None, cycle_id=None, date=None):
        self.farm_id = farm_id
        self.pond_id = pond_id
        self.cycle_id = cycle_id
        self.date = date

    def get_profit_lost_metric(self, df: pd.DataFrame, last_doc: int) -> dict:
        """get profit lost metric

        Args:
            df (pd.DataFrame): basis dataframe
            last_doc (int): maximal doc

        Returns:
            dict: dictionary of profit and lost data
        """
        potential_profit = (
            df["potential_revenue"].iloc[-1].round()
            - df["cum_total_cost"].iloc[-1].round()
        )
        profit_n_lost = {
            "title": Constant.TITLE_PROFIT_AND_LOST,
            "data": [
                {
                    "title": "DOC",
                    "value": float(last_doc),
                    "unit": "days",
                },
                {
                    "title": Constant.TITLE_TOTAL_COST,
                    "value": f'Rp {df["cum_total_cost"].iloc[-1].round():,}',
                },
                {
                    "title": Constant.TITLE_TOTAL_REVENUE,
                    "value": f'Rp {df["potential_revenue"].iloc[-1].round():,}',
                },
                {
                    "title": Constant.TITLE_TOTAL_PROFIT,
                    "value": f"Rp {potential_profit:,}",
                },
                {
                    "title": Constant.TITLE_COST_PER_KILO,
                    "value": f'Rp {df["cost_per_kg"].iloc[-1].round():,}',
                },
            ],
        }

        return profit_n_lost

    def get_cost_breakdown_data(self, df: pd.DataFrame):
        """cost breakdown

        Args:
            df (pd.DataFrame): historical data of cycle
        """
        colors = [
            "#104C9C",
            "#E71D7A",
            "#EE7859",
            "#FAB72D",
            "#F0E419",
            "#4CAF46",
            "#D0D0D0",
        ]

        # color management and select the cost data
        if "cost_seed" in df.columns:
            cost_df = df[Column.day_cost_columns + ["cost_seed"]].cumsum().iloc[-1]
            colors.append("#C4B0FF")
        else:
            cost_df = df[Column.day_cost_columns].cumsum().iloc[-1]

        # generate the table cost
        table_cost = pd.DataFrame(
            {
                "item": cost_df.index.str.replace("cost_", "").tolist(),
                "value": cost_df.tolist(),
                "color": colors,
            }
        )

        # cost plot
        table_cost = table_cost[["item", "value"]]
        table_cost.columns = ["name", "value"]
        table_cost["value"] = table_cost["value"].round(2)

        cost_plot = Pie(
            title="",
            data=table_cost.to_dict("records"),
            doughnut=True,
            legend=False,
        ).plot()

        cost_plot["color"] = colors
        cost_plot["tooltip"]["formatter"] = "<b>{b}</b> : {d}%"
        table_cost["value"] = table_cost["value"].round(2).map("{:,.0f}".format)
        return table_cost, cost_plot

    def get_production_status_data(self, df: pd.DataFrame, doc: list):
        """production status

        Args:
            df (pd.DataFrame): historical data of cycle
            doc (list): list of Daily of Culture
        """

        # generate the biomass plot
        biomass_plot = Line(
            title="",
            x=doc,
            y=[
                df["harvest_biomass_kg"].round(2).tolist(),
                df["biomass_kg"].round(2).tolist(),
            ],
            labels=["Harvested Biomass", "Biomass"],
        ).plot()
        biomass_plot["color"] = ["#474DA4", "#FBBC05"]

        # set the recent production status
        df["cum_harvested_biomass"] = df["harvest_biomass_kg"].cumsum()
        current_harvested_biomass = round(df["cum_harvested_biomass"].iloc[-1])
        current_total_biomass = round(df["total_biomass"].iloc[-1])
        current_pond_biomass = round(df["biomass_kg"].iloc[-1])
        current_abw = round(df["adj_abw"].iloc[-1], 2)

        # set the production status data
        prod_status_data = [
            {
                "title": Constant.TITLE_HARVESTED_BIOMASS,
                "value": f"{current_harvested_biomass:,}",
                "unit": Unit.kg,
                "description": Constant.HARVESTED_BIOMASS_DESCRIPTION,
            },
            {
                "title": Constant.TITLE_BIOMASS,
                "value": f"{current_total_biomass:,}",
                "unit": Unit.kg,
                "description": Constant.TOTAL_BIOMASS_DESCRIPTION,
            },
            {
                "title": Constant.TITLE_POND_BIOMASS,
                "value": f"{current_pond_biomass:,}",
                "unit": Unit.kg,
                "description": Constant.POND_BIOMASS_DESCRIPTION,
            },
        ]

        # condition wheter agregate or not
        if self.cycle_id:
            prod_status_data.append(
                {
                    "title": Constant.TITLE_ABW,
                    "value": f"{current_abw:,}",
                    "unit": Unit.gr,
                    "description": Constant.AVERAGE_BODY_WEIGHT_DESCRIPTION,
                }
            )

        return {
            "title": Constant.TITLE_PRODUCTION_STATUS,
            "data": prod_status_data,
            "plot": biomass_plot,
        }

    def economic(self):
        """economic data"""
        try:
            # generate the selected data
            df, group_df = get_selected_data(
                self.farm_id, self.pond_id, self.cycle_id, self.date
            )

            # check the data is not empty
            if len(group_df) == 0:
                raise AttributeError("There is no active cycle data")

            # generate profit and lost metric
            profit_n_lost = self.get_profit_lost_metric(df, last_doc=group_df[0]["doc"].max())
            # generate cost metric and the plot
            table_cost, cost_plot = self.get_cost_breakdown_data(df)
            # generate metric of production status
            production_status = self.get_production_status_data(
                df, doc=group_df[0]["doc"].tolist()
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
            InvalidQueryError,
            LookupError,
        ) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "profit_n_lost": profit_n_lost,
                "cost_breakdown": {
                    "title": Constant.TITLE_COST_BREAKDOWN,
                    "table": {
                        "columns": table_cost.columns.tolist(),
                        "data": table_cost.to_dict("records"),
                    },
                    "plot": cost_plot,
                },
                "production_status": production_status,
            },
        )

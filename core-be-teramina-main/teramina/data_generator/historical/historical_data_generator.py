# pylint: disable=R0801, R0914

import pandas as pd
import numpy as np

from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.feeding.models.feed_realization_model import FeedRealization

from teramina.formulas.revenue.revenue_formula import Revenue
from teramina.formulas.cost.cost_formula import Cost

from teramina.helpers.constant_column import Column
from teramina.helpers.constant_value import Constant
from teramina.helpers.data_preprocessor import waterquality_columns_checker
from teramina.helpers.shrimp_price import get_price_array
from teramina.data_generator.helpers.data_completion import (
    set_cost_data,
    set_revenue_data,
)
from teramina.data_generator.helpers.utils import (
    set_params_config,
    parse_harvest_data_input,
)
from teramina.data_generator.historical.utils import (
    set_carriying_capacity,
    parse_tray_data_input,
)


class HistoricalDataGenerator:
    """Historical Data Generator"""

    def __init__(self, cycle_id) -> None:
        self.cycle_id = cycle_id

    def get_object_data(self, df: pd.DataFrame, ph: list, partial_doc: list, **kwargs):
        """Get object of data
        Args:
            df (pd.DataFrame): farming data
            ph (list): partial harvest value
            partial_doc (list): doc of partial harvest
            **kwargs: keyword argument.

        Keyword Arguments:
            - (bool) is_docfinal_similar_with_last: doc final condition
            - (bool) is_final_harvest_defined: wether final harvest was defined or not
            - (int) t: time t
            - (int) t0: initial t

        Returns:
            tuple: tuple of object revenue and cost
        """
        is_docfinal_similar_with_last = kwargs.get("is_docfinal_similar_with_last")
        is_final_harvest_defined = kwargs.get("is_final_harvest_defined")

        (
            init_data,
            population_config,
            growth_config,
            cost_config,
        ) = set_params_config(df, ph, partial_doc, docfinal=df["doc"].max())

        # get the price data from API
        price_array = get_price_array(self.cycle_id)

        # prepare tray data from feed realization
        trays = parse_tray_data_input(
            FeedRealization.objects(cycle_id=self.cycle_id)
            .only("doc", "feed_leftover")
            .all()
        )

        # compute revenue
        revenue = Revenue(
            population_config=population_config,
            growth_config=growth_config,
            df=df,
            t=kwargs.get("t"),
            t0=kwargs.get("t0"),
            required_columns=Column.dependent_columns,
            is_docfinal_similar_with_last=is_docfinal_similar_with_last,
            is_forecast=False,
            is_ph_as_biomass=bool(ph),
            is_final_harvest_defined=is_final_harvest_defined,
            price_array=price_array,
        )

        # compute cost
        cost = Cost(
            df=df,
            t=kwargs.get("t"),
            t0=kwargs.get("t0"),
            required_columns=Column.dependent_columns,
            cost_config=cost_config,
            population_config=population_config,
            growth_config=growth_config,
            is_docfinal_similar_with_last=is_docfinal_similar_with_last,
            is_forecast=False,
            is_ph_as_biomass=bool(ph),
            is_final_harvest_defined=is_final_harvest_defined,
            trays=trays,
            feed_temp_data=pd.read_csv(Constant.FR_TEMPERATURE_DATA_PATH),
            protein_content=init_data["protein_content"],
        )

        return revenue, cost

    def generate_historical_result(
        self, df: pd.DataFrame, is_docfinal_similar_with_last=True
    ) -> pd.DataFrame:
        """generate historical data

        Args:
            df (pd.DataFrame): _description_
            is_docfinal_similar_with_last (bool, optional): _description_. Defaults to True.

        Returns:
            pd.DataFrame: _description_
        """

        harvest = (
            HarvestRecord.objects(cycle_id=self.cycle_id).only("harvest_data").first()
        )
        if harvest:
            harvest_data = parse_harvest_data_input(harvest.harvest_data)
            ph = harvest_data["partial_harvest"]
            partial_doc = harvest_data["partial_doc"]
            is_final_harvest_defined = harvest_data["is_final_harvest_defined"]
            realized_revenue = harvest_data["revenue"]
        else:
            ph = []
            partial_doc = []
            realized_revenue = []
            is_final_harvest_defined = False

        # generate data object
        revenue, cost = self.get_object_data(
            df=df,
            ph=ph,
            partial_doc=partial_doc,
            t=df["doc"].max(),
            t0=df["doc"].min() - 1,
            is_docfinal_similar_with_last=is_docfinal_similar_with_last,
            is_final_harvest_defined=is_final_harvest_defined,
        )

        sampling_columns = df.filter(like="sampling_").columns.tolist()
        cols = Column.required_columns + sampling_columns
        wq_columns = waterquality_columns_checker(df.columns.tolist())
        cols = cols + wq_columns
        # initialize new dataframe with regarding to the feed given
        if "feed_given" in df.columns:
            cols = cols + ["feed_given"]

        ndf = df[cols].copy()
        # set revenue data into the dataframe
        ndf = set_revenue_data(ndf, revenue)
        # set revenue data into the dataframe
        ndf = set_cost_data(ndf, cost)
        # add carriying capacity
        ndf = set_carriying_capacity(ndf, self.cycle_id, cost)

        # update with realized revenue record
        if realized_revenue:
            for doc, rev in zip(partial_doc, realized_revenue):
                ndf.loc[doc - 1, "realized_revenue"] = rev

        # update the cumsum of realized revenue
        ndf["cum_feed"] = np.cumsum(ndf["feed_given"])
        ndf["cum_total_cost"] = np.cumsum(ndf["total_cost"])
        ndf["cum_realized_revenue"] = np.cumsum(ndf["realized_revenue"])
        ndf.eval("profit = cum_realized_revenue - cum_total_cost", inplace=True)
        ndf.eval(
            "potential_profit = profit + potential_revenue - cum_total_cost",
            inplace=True,
        )
        return ndf

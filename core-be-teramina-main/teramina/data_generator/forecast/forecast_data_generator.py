# pylint: disable=R0801, E0401, E1137

import pandas as pd
import numpy as np

from teramina.formulas.cost.cost_formula import Cost
from teramina.helpers.constant_column import Column
from teramina.helpers.constant_value import Constant
from teramina.helpers.shrimp_price import get_price_array

from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.formulas.revenue.revenue_formula import Revenue
from teramina.formulas.weight.weight_kalman import WeightKalman

from teramina.data_generator.historical.historical_data_generator import (
    HistoricalDataGenerator,
)
from teramina.data_generator.optimization_data_generator import OptimalDataGenerator
from teramina.data_generator.forecast.forecast_data_dummy_generator import ForecastData

from teramina.data_generator.forecast.utils import (
    parse_harvest_data_simulation,
    generate_harvest_data,
    update_harvest_recommendation_table,
)
from teramina.data_generator.helpers.data_completion import (
    set_cost_data,
    set_revenue_data,
)
from teramina.data_generator.helpers.utils import set_params_config


class ForecastDataGenerator(HistoricalDataGenerator):
    """Forecasted data generator"""

    def __init__(self, cycle_id) -> None:
        self.cycle_id = cycle_id

        super().__init__(cycle_id=cycle_id)

        # set the harvest record data
        self.harvest_record = (
            HarvestRecord.objects(cycle_id=cycle_id).only("harvest_data").first()
        )

    def __is_partial_harvest_completed_for_cycle(self) -> bool:
        """This function is used to ensure whether the partial harvest has been completed or not.

        Returns:
            bool: True when completed. False when not completed.
        """

        if self.harvest_record:
            harvest_data = parse_harvest_data_simulation(
                self.harvest_record.harvest_data
            )
            if harvest_data["is_final_harvest_defined"]:
                return True

            if len(harvest_data["partial_doc"]) >= Constant.MAX_PARTIAL_HARVEST:
                # greater than or equal because maybe the final harvest included
                return True

        return False

    def __restructure_harvest_record(
        self, new_partial_doc: list, new_partial_harvest: list
    ) -> tuple:
        """Function that used to restructuring partial harvest data
            based on harvest record (realization).

        Args:
            cycle_id (str): cycle id
            new_partial_doc (list): list of DOC that partial harvest happens
            new_partial_harvest (list): list amount of partial harvest

        Returns:
            tuple: partial_doc (list), partial_harvest (list)
        """
        if self.harvest_record:
            harvest_data = parse_harvest_data_simulation(
                self.harvest_record.harvest_data
            )
            partial_doc = np.array(harvest_data["partial_doc"])
        else:
            partial_doc = []

        idx = np.where(np.logical_not(np.isin(new_partial_doc, partial_doc)))
        return new_partial_doc[idx], new_partial_harvest[idx]

    def __applied_optimal_harvest_strategy(
        self, df: pd.DataFrame, t0: int, max_t: int, wt: np.ndarray, **kwargs
    ) -> dict:
        """optimal harvesting strategy

        Args:
            df (pd.DataFrame): historical dataframe
            t0 (int): initial t for exploration
            max_t (int): the last t for exaploration
            wt (np.ndarray): weight
            kwargs**: keyword argument
                is_simulation (bool): simulation status

        Returns:
            (tuple): tuple of forecast_docfinal, ph, partial_doc, wt
        """

        # unpack the keyword argument
        is_simulation = kwargs.get("is_simulation")

        # get harvesting optimal data
        opt_data = OptimalDataGenerator(self.cycle_id).get_optimal_harvest(df)

        if max_t > opt_data["doc_final"]:
            wt = wt[: opt_data["doc_final"] - t0]

        forecast_docfinal = max_t
        if not is_simulation:
            forecast_docfinal = opt_data["doc_final"]

        # generate the formatted harvest data
        harvest_data = generate_harvest_data(
            opt_data["historical_ph"],
            opt_data["historical_partial_doc"],
            opt_data["forecast_ph"],
            opt_data["forecast_partial_doc"],
        )

        # update the harvest recommendation data
        update_harvest_recommendation_table(self.cycle_id, harvest_data)

        return (
            forecast_docfinal,
            opt_data["forecast_partial_harvest_without_final_doc"],
            opt_data["forecast_partial_doc_without_final_doc"],
            wt,
        )

    def generate_alpha_from_historical(self, historical_df: pd.DataFrame):
        """generate alpha from historical"""
        growth = WeightKalman(
            df=historical_df,
            t=historical_df["doc"].iloc[-1],
            conditions=[
                [],
                [
                    Constant.NH3_SUITABLE_MIN,
                    Constant.NH3_OPTIMAL_MIN,
                    Constant.NH3_OPTIMAL_MAX,
                    Constant.NH3_SUITABLE_MAX,
                ],
                [
                    Constant.DO_SUITABLE_MIN,
                    Constant.DO_OPTIMAL_MIN,
                    Constant.DO_OPTIMAL_MAX,
                    Constant.DO_SUITABLE_MAX,
                ],
            ],
            required_columns=["temperature", "do", "nh3", "abw"],
            t0=historical_df["doc"].iloc[0],
            w0=historical_df["adj_abw"].iloc[0],
            wn=Constant.WN,
        )
        alpha = growth.fit()
        return alpha

    def __calculate_weight_estimation(self, growth: WeightKalman, alpha: list) -> tuple:
        """Weight estimation using Extended Kalman Filter

        Args:
            growth (object): Growth object is growth definition from class Growth
            alpha (list): parameter alpha that used in counting weight
        Returns:
            tuple: wt, alphas
        """

        t = growth.t
        t0 = growth.t0

        alpha1, alpha2, alpha3, alpha4 = alpha
        # find the measurement
        wt = growth.wt(growth.base_data, alpha1, alpha2, alpha3, alpha4)

        # filtering using kalman filter
        # define measurement noise
        V = 0.000001
        # define estimation noise
        W = 0.0001
        # define parameter noise
        r = 0.000001

        # define error covariance
        p_init = [0.01, np.eye(4) * 0.01]

        # estimates
        wt, alphas = growth.joint_estimation_wt(
            measurement=wt, alpha=alpha, t0=t0, t=t, v=V, w=W, r=r, p_init=p_init
        )

        return wt, alphas

    def __set_simulation_data(self, partial_harvest_data: dict) -> tuple:
        """setup the simulation data when simulation used.

        Args:
            partial_harvest_data (dict): dict partial_havest_data input

        Returns:
            tuple: partial_doc (list), ph (list), forecast_docfinal (int),
                is_final_harvest_defined (bool), is_ph_as_biomass (bool)
        """
        # based on the UX when simulation ph is in biomass unit not in population
        is_ph_as_biomass = True

        partial_harvest_object = parse_harvest_data_simulation(partial_harvest_data)

        partial_doc = partial_harvest_object["partial_doc"]
        partial_harvest = partial_harvest_object["partial_harvest"]
        forecast_docfinal = partial_harvest_object["final_doc"]
        is_final_harvest_defined = partial_harvest_object["is_final_harvest_defined"]

        # restructuring simulation with harvest record data
        partial_doc, ph = self.__restructure_harvest_record(
            np.array(partial_doc),
            np.array(partial_harvest),
        )

        return (
            partial_doc,
            ph,
            forecast_docfinal,
            is_final_harvest_defined,
            is_ph_as_biomass,
        )

    def __get_forecast_object_data(self, **kwargs):
        # unpack keyword oarguments
        historical_df = kwargs.get("historical_df")
        forecast_df = kwargs.get("forecast_df")
        wt = kwargs.get("wt")
        forecast_t0 = kwargs.get("forecast_t0")
        forecast_docfinal = kwargs.get("forecast_docfinal")
        is_ph_as_biomass = kwargs.get("is_ph_as_biomass")
        is_final_harvest_defined = kwargs.get("is_final_harvest_defined")

        # parameter initialization
        (
            init_data,
            population_config,
            growth_config,
            cost_config,
        ) = set_params_config(
            historical_df,
            kwargs.get("ph"),
            kwargs.get("partial_doc"),
            forecast_docfinal,
        )
        # update the population config
        population_config["initial_stocking"] = historical_df["population"].iloc[-1]
        # update the growth config
        growth_config["w0"] = historical_df["abw"].iloc[-1]

        # initialize the revenue object
        forecast_revenue = Revenue(
            population_config=population_config,
            growth_config=growth_config,
            df=forecast_df,
            wt_forecast=wt,
            t=forecast_docfinal,
            t0=forecast_t0,
            required_columns=Column.dependent_columns,
            is_docfinal_similar_with_last=True,
            is_forecast=True,
            is_ph_as_biomass=is_ph_as_biomass,
            is_final_harvest_defined=is_final_harvest_defined,
            price_array=get_price_array(self.cycle_id),
        )

        # initialize the cost object
        forecast_cost = Cost(
            df=forecast_df,
            wt_forecast=wt,
            t=forecast_docfinal,
            t0=forecast_t0,
            required_columns=Column.dependent_columns,
            cost_config=cost_config,
            population_config=population_config,
            growth_config=growth_config,
            is_docfinal_similar_with_last=True,
            is_forecast=True,
            is_ph_as_biomass=is_ph_as_biomass,
            is_final_harvest_defined=is_final_harvest_defined,
            trays=None,
            feed_temp_data=pd.read_csv(Constant.FR_TEMPERATURE_DATA_PATH),
            protein_content=init_data["protein_content"],
        )

        return forecast_revenue, forecast_cost

    def get_forecasted_wt(self, df: pd.DataFrame, max_doc: int) -> tuple:
        """generate the forecasted weight of shrimp

        Args:
            df (pd.DataFrame): historical data of shrimp farming
            max_doc (int): maximal doc

        Returns:
            tuple: forecast_t0 (int): initial forecasted doc,
                forecast_df (pd.DataFrame): forecasted dataframe,
                wt (np.ndarray) : weight, alphas (list) : parameter
        """

        if np.isnan(df["abw"].iloc[-1]):
            w0 = df["adj_abw"].iloc[-1]
        else:
            w0 = df["abw"].iloc[-1]

        forecast_object = ForecastData.get_forecast_df(df)
        forecast_df = forecast_object["table"]
        forecast_df["abw"] = np.nan
        forecast_t0 = int(forecast_object["historical_docfinal"])

        growth = WeightKalman(
            df=forecast_df,
            t=max_doc,
            conditions=[
                [],
                [
                    Constant.NH3_SUITABLE_MIN,
                    Constant.NH3_OPTIMAL_MIN,
                    Constant.NH3_OPTIMAL_MAX,
                    Constant.NH3_SUITABLE_MAX,
                ],
                [
                    Constant.DO_SUITABLE_MIN,
                    Constant.DO_OPTIMAL_MIN,
                    Constant.DO_OPTIMAL_MAX,
                    Constant.DO_SUITABLE_MAX,
                ],
            ],
            required_columns=["temperature", "do", "nh3", "abw"],
            t0=forecast_t0,
            w0=w0,
            wn=Constant.WN,
        )

        alpha1, alpha2, alpha3, alpha4 = self.generate_alpha_from_historical(
            historical_df=df
        )

        if all(i == 0 for i in (alpha1, alpha2, alpha3, alpha4)):
            alpha1, alpha2, alpha3, alpha4 = 0.0001, 0.0002, 0.006, 0.0015

        # estimate using EKF
        wt, alphas = self.__calculate_weight_estimation(
            growth, [alpha1, alpha2, alpha3, alpha4]
        )

        return forecast_t0, forecast_df, wt, alphas

    def generate_forecast_result(
        self,
        historical_df: pd.DataFrame,
        forecast_docfinal=Constant.MAX_DOC,
        **kwargs,
    ):
        """get forecasted data

        Args:
            historical_df (pd.DataFrame): _description_
            forecast_docfinal (_type_, optional): _description_. Defaults to Constant.MAX_DOC.
            kwargs : keyword arguments
                use_harvest_recommendation (bool): wether used recommendation or not
                is_simulation (bool): wether simulation condition or not
                partial_harvest_data (dict): data of partial harvest


        Returns:
            ndf: forecasted dataframe
        """

        # Ensure that we could forecasting based on the partial harvest condition
        if self.__is_partial_harvest_completed_for_cycle():
            return False

        # generate forecasted wt
        forecast_t0, forecast_df, wt, alphas = self.get_forecasted_wt(
            historical_df, forecast_docfinal
        )

        # define the default value of ph and partial_doc
        ph = []
        partial_doc = []

        # update the value of ph and partial_doc if harvest recommendation applied
        if kwargs.get("use_harvest_recommendation", False):
            optimal_harvest_strategy = self.__applied_optimal_harvest_strategy(
                historical_df,
                forecast_t0,
                forecast_docfinal,
                wt,
                is_simulation=kwargs.get("is_simulation", False),
            )
            ph = optimal_harvest_strategy[1]
            partial_doc = optimal_harvest_strategy[2]
            forecast_docfinal = optimal_harvest_strategy[0]
            wt = optimal_harvest_strategy[3]

        # handler wether a simulation or not
        is_ph_as_biomass = False
        is_final_harvest_defined = False
        if kwargs.get("partial_harvest_data", None):
            (
                partial_doc,
                ph,
                forecast_docfinal,
                is_final_harvest_defined,
                is_ph_as_biomass,
            ) = self.__set_simulation_data(kwargs.get("partial_harvest_data", None))

        # generate object generator data
        forecast_object_data = self.__get_forecast_object_data(
            historical_df=historical_df,
            forecast_df=forecast_df,
            wt=wt,
            ph=ph,
            partial_doc=partial_doc,
            forecast_t0=forecast_t0,
            forecast_docfinal=forecast_docfinal,
            is_ph_as_biomass=is_ph_as_biomass,
            is_final_harvest_defined=is_final_harvest_defined,
        )

        # generate the result
        ndf = pd.DataFrame()
        # add revenue data to the dataframe
        ndf = set_revenue_data(ndf, forecast_object_data[0], True)
        # add parameter to the dataframe
        alphas = np.array(alphas)[: (forecast_docfinal - forecast_t0)]
        ndf[["alpha1", "alpha2", "alpha3", "alpha4"]] = alphas
        # add cost data to the dataframe
        ndf = set_cost_data(ndf, forecast_object_data[1])

        ndf["doc"] = (
            np.arange(forecast_object_data[0].t0, forecast_object_data[0].t) + 1
        )

        return ndf

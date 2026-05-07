# pylint: disable=unsubscriptable-object
import pandas as pd

from .combined_data_generator import CombinedDataGenerator
from ..cycle_data.models.cycle_data_model import ForecastData
from ..helpers.constant_value import Constant


class CombinedDataSimulator(CombinedDataGenerator):
    """Combined data generator for simulation function"""

    def __init__(self, cycle_id, partial_harvest):
        self.cycle_id = cycle_id
        self.partial_harvest = partial_harvest

        super().__init__(cycle_id)

    def generate_simulation_data(self, is_simulation: bool = True) -> pd.DataFrame:
        """generate simulation's data"""
        cycle_data = (
            ForecastData.objects(cycle_id=self.cycle_id).only("result_data").first()
        )
        if not cycle_data:
            raise ValueError(
                "Forecasted data is not ready because we need more existing data."
            )

        df = pd.DataFrame(cycle_data.result_data)
        df1 = df.query("category == 'historical' ")

        # add origin biomass
        df1.eval("origin_biomass = population * abw / 1000", inplace=True)

        final_doc = self.partial_harvest["final"]["doc"]
        if final_doc == "":
            final_doc = Constant.MAX_DOC

        if final_doc <= df1["doc"].iloc[-1]:
            doc = df1["doc"].iloc[-1]
            raise KeyError(
                f"Simulation error: Last data DOC ({doc}) and final DOC ({final_doc}) don’t match."
            )

        # generate the simulation result
        df2 = self.generate_forecast_result(
            historical_df=df1,
            forecast_docfinal=final_doc,
            use_harvest_recommendation=False,
            is_simulation=is_simulation,
            partial_harvest_data=self.partial_harvest,
        )

        # combining the historical and the forecasted data
        res = self.set_combined_data(df1, df2)
        return res

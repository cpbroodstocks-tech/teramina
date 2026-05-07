# pylint: disable=E0401
import pandas as pd
import numpy as np
from mongoengine.errors import FieldDoesNotExist

from teramina.harvest.schemas.harvest_schema import HarvestDataSchema
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema
from teramina.harvest.models.harvest_recommendation_model import HarvestRecommendation
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.cycle_data.models.cycle_data_model import (
    CycleData,
    ResultData,
    ForecastData,
)

from teramina.data_generator.combined_data_generator import CombinedDataGenerator
from teramina.data_generator.combined_data_simulator import CombinedDataSimulator

from teramina.helpers.database_updater import (
    update_forecast_combined_data_result,
    update_historical_data_result,
    set_last_updated,
)
from teramina.helpers.constant_value import Constant


class HarvestService:
    """Harvest Service

    Manage harvest actions

    """

    def __init__(self, cycle_id):
        self.cycle_id = cycle_id

    def __check_if_culture_conditions_are_met(
        self, is_simulation=False, harvest_data: dict = None, last_doc: int = None
    ):
        """culture condition checker

        Args:
            is_simulation (bool, optional): in context of simulation or not. Defaults to False.
            harvest_data (dict, optional): is there is harvest data. Defaults to None.
            last_doc (int, optional): last doc. Defaults to None.

        Raises:
            ValueError: When there is an error

        Returns:
            str: only return message as a string when there is an harvest record data
        """
        harvest_record = HarvestRecord.objects(cycle_id=self.cycle_id).first()
        if harvest_record:
            if harvest_record.harvest_data["final"]["doc"] != "":
                raise ValueError("Can't forecast after finishing harvest")

            if is_simulation:
                harvest_values = [
                    i["doc"]
                    for i in harvest_record.harvest_data.values()
                    if i["doc"] != ""
                ]
                if last_doc and any(i["doc"] < last_doc for i in harvest_data.values()):
                    return "You used bad data. Data should be before the final daily of culture"

                if any(i["doc"] in harvest_values for i in harvest_data.values()):
                    return (
                        "Record data will overwrite simulation data with the same date."
                    )

                return None

            return None

        return None

    def __validate_doc_value(self, doc_value: int, doc: set):
        """DOC's value validation

        Args:
            doc_value (int): DOC value from the harvest record input
            doc (set): set of DOC values from the harvest record input
        """

        if not isinstance(doc_value, (int, float)):
            raise ValueError(
                "Wrong data. The DOC’s data should be a number or a empty string ('')."
            )

        if doc_value == "":
            raise ValueError(
                "Error in input value. Please make sure that you have input the DOC's value."
            )

        if doc_value < 0:
            raise ValueError("You are not permitted to add DOC with lower than zero.")

        if doc_value in doc:
            raise ValueError(f"Your harvest data for the DOC {doc_value} was added.")

        if doc:
            max_previous_doc = max(doc)
            if doc_value < max_previous_doc:
                raise ValueError(
                    "Error: The DOC in the harvest data is not incremented."
                )

    def __validate_biomass_value(self, biomass_value: float):
        """Biomass's value validation

        Args:
            biomass_value (float): biomass's value from harvest record input
        """
        if not isinstance(biomass_value, (int, float)):
            raise ValueError(
                "Wrong data. The DOC’s data should be a number or an empty string ('')."
            )

        if biomass_value is not None and biomass_value < 0:
            raise ValueError("Error: Bad biomass. No biomass data below zero allowed.")

    def __validate_based_on_historical_data(
        self, doc_val: int, current_doc: int, biomass: set
    ):
        """Validation value of doc and biomass based on historical data

        Args:
            doc_val (int): DOC's value from harvest record input
            current_doc (int): current DOC
            biomass (set): set of biomass value

        Raises:
            ValueError: _description_
            ValueError: _description_
        """
        if doc_val > current_doc:
            raise ValueError(
                f"Current DOC is {current_doc}. No harvest for DOC {doc_val}."
            )

        actual_data = (
            ResultData.objects(cycle_id=self.cycle_id)
            .only("result_data")
            .first()
            .result_data
        )
        if actual_data[doc_val - 1]["total_biomass"] - sum(biomass) < 0:
            raise ValueError(
                "Can't harvest more than expected amount of biomass in the pond"
            )

    def harvest_data_validation(
        self, current_doc: int, harvest_data: dict, is_simulation=False
    ):
        """harvest data input validation

        Args:
            current_doc (int): current doc
            harvest_data (dict): harvest record input
            is_simulation (bool, optional): True when it's used for simulation. Defaults to False.
        """
        doc = set()
        biomass = set()

        for data in harvest_data.values():
            doc_val = data.get("doc", None)
            biomass_val = data.get("biomass", None)
            revenue = data.get("revenue", None)

            if (doc_val == "") and (biomass_val == "") and (revenue == ""):
                continue

            self.__validate_doc_value(doc_val, doc)
            self.__validate_biomass_value(biomass_val)

            biomass.add(biomass_val)
            if not is_simulation:
                self.__validate_based_on_historical_data(doc_val, current_doc, biomass)

            doc.add(doc_val)

    def __base_table_formatter(self, harvest_data: dict, df: pd.DataFrame) -> dict:
        """the basis table formatter function

        Args:
            harvest_data (dict): harvesting data
            df (pd.DataFrame): dataframe

        Returns:
            dict: the exported dictionary from dataframe that contains fields and rows
        """
        rows_data = []

        idx = 0
        for x in harvest_data.keys():
            doc = harvest_data[x]["doc"]
            bio = harvest_data[x]["biomass"]

            if (bio != "") and (doc != ""):
                if x != "final":
                    harvest_type = "partial"
                else:
                    harvest_type = "final"

                biomass = df["harvest_biomass_kg"].iloc[doc - 1].round().astype(int)
                revenue = df["realized_revenue"].iloc[doc - 1].round().astype(int)
                profit = df["profit"].iloc[doc - 1].round().astype(int)
                size = 1000 / df["adj_abw"].iloc[doc - 1]

                idx = idx + 1
                rows_data.append(
                    {
                        "harvest_no": idx,
                        "harvest_type": harvest_type,
                        "doc": doc,
                        "biomass_kg": f"{biomass:,} kg",
                        "size": round(size, 2),
                        "revenue": f"IDR {revenue:,}",
                        "profit": f"IDR {profit:,}",
                    }
                )

        return {"fields": Constant.HARVEST_FIELDS, "rows": rows_data}

    def harvest_table_formatter(
        self, harvest_data: dict, is_historical: bool = True
    ) -> dict:
        """Harvest table formatter

        Args:
            harvest_data (dict): Harvest data dictionaries
            is_historical (bool, optional): is the data histories?. Defaults to True.

        Raises:
            ValueError: The conditional raised when the result data is None or Null

        Returns:
            dict: the exported dictionary from dataframe that contains fields and rows
        """

        if is_historical:
            result_data = ResultData.objects(cycle_id=self.cycle_id).first()
        else:
            result_data = ForecastData.objects(cycle_id=self.cycle_id).first()

        if not result_data:
            raise ValueError(f"Data from cycle with id {self.cycle_id} doesn't exist")

        df = pd.DataFrame(result_data.result_data)
        return self.__base_table_formatter(harvest_data, df)

    def get_harvest_record(self):
        """get the harvest record data"""
        try:
            harvest = HarvestRecord.objects(cycle_id=self.cycle_id).first()
            result_table = ResultData.objects(cycle_id=self.cycle_id).first()
            if result_table:
                last_doc = result_table.result_data[-1]["doc"]
            else:
                raise AttributeError(f"Data with cycle {self.cycle_id} doesn't exist")
            if harvest:
                harvest_data = harvest.harvest_data
                result_data = self.harvest_table_formatter(harvest_data, True)
                result_data["cycle_info"] = {"last_doc": last_doc}
            else:
                result_data = {"fields": Constant.HARVEST_FIELDS, "rows": []}
                result_data["cycle_info"] = {"last_doc": last_doc}

        except (FieldDoesNotExist, ValueError, AttributeError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Getting harvested data for cycle - {self.cycle_id} successfully",
            payload=result_data,
        )

    def add_harvest_record(self, data: HarvestDataSchema):
        """add new harvest data"""
        try:
            cycle_data = CycleData.objects(cycle_id=self.cycle_id).first()

            if cycle_data:
                df = pd.DataFrame(cycle_data.result_data)
                current_doc = df["doc"].iloc[-1]

                data = {
                    "partial1": data.partial1,
                    "partial2": data.partial2,
                    "partial3": data.partial3,
                    "final": data.final,
                }

                self.harvest_data_validation(current_doc, data, False)

                harvest_record = HarvestRecord.objects(cycle_id=self.cycle_id)
                if harvest_record:
                    harvest_record.update(
                        set__cycle_id=self.cycle_id, set__harvest_data=data
                    )
                else:
                    harvest = HarvestRecord(cycle_id=self.cycle_id, harvest_data=data)
                    harvest.save()

                # update the combined data result
                combined_df = CombinedDataGenerator(self.cycle_id).generate_data(df)

                historical_df = combined_df.query(
                    "category == 'historical'"
                ).reset_index(drop=True)

                update_historical_data_result(self.cycle_id, historical_df)
                if historical_df.shape[0] > 1:
                    update_forecast_combined_data_result(self.cycle_id, combined_df)

                # set last update data
                set_last_updated(self.cycle_id)

                # set last update data
                set_last_updated(self.cycle_id)

        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except ValueError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Adding harvested record data for cycle - {self.cycle_id} successfully",
            payload={},
        )

    def get_harvest_recommendation(self):
        """generate harvest recommendation data"""
        try:
            harvest_record = HarvestRecord.objects(cycle_id=self.cycle_id).first()
            harvest_recommendation = HarvestRecommendation.objects(
                cycle_id=self.cycle_id
            ).first()
            if (harvest_record is not None) & (harvest_recommendation is not None):
                harvest_record = harvest_record.harvest_data
                if (harvest_record["final"]["doc"] != "") & (
                    harvest_record["final"]["biomass"] != ""
                ):
                    harvest_data = harvest_record
                else:
                    harvest_data = harvest_recommendation.harvest_data
            elif harvest_recommendation:
                harvest_data = harvest_recommendation.harvest_data
            else:
                raise FieldDoesNotExist("Harvest recommendation data doesn't exist")

            result_data = self.harvest_table_formatter(harvest_data, False)
            # make sure that last index to be final harvest
            result_data["rows"][-1]["harvest_type"] = "final"

        except ValueError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except IndexError:
            return 400, DataErrorSchema(
                code=400, message="it's seem that you still under than 60th DOC"
            )

        except FieldDoesNotExist as exception:
            return 200, DataSuccessSchema(
                code=200,
                message=str(exception),
                payload={"fields": Constant.HARVEST_FIELDS, "rows": []},
            )

        return 200, DataSuccessSchema(
            code=200,
            message="Getting harvested recommendation data success",
            payload=result_data,
        )

    def add_harvest_simulation(self, data: HarvestDataSchema):
        """create harvest simulation"""
        try:
            cycle_data = CycleData.objects(cycle_id=self.cycle_id).first()

            if cycle_data:
                df = pd.DataFrame(cycle_data.result_data)
                last_doc = df["doc"].iloc[-1]

                data = {
                    "partial1": data.partial1,
                    "partial2": data.partial2,
                    "partial3": data.partial3,
                    "final": data.final,
                }

                # ensuring the culture condition met the qualification
                message = self.__check_if_culture_conditions_are_met(
                    True, data, last_doc
                )
                message = (
                    "Your data still under 30, we set parameters by default."
                    if df.shape[0] <= 30
                    else None
                )

                self.harvest_data_validation(last_doc, data, True)

                df = CombinedDataSimulator(
                    self.cycle_id, data
                ).generate_simulation_data(is_simulation=True)
                df = df.replace({np.nan: None})

                result_data = self.__base_table_formatter(data, df)
                result_data["message"] = message
            else:
                raise AttributeError(
                    f"The data associated with the cycle_id {self.cycle_id} could not be found. "
                )

        except (FieldDoesNotExist, KeyError, ValueError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except AttributeError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Getting harvested simulation data for cycle - {self.cycle_id} successfully",
            payload=result_data,
        )

    def delete_harvest_record(self):
        """delete harvest record in a cycle"""
        try:
            HarvestRecord.objects(cycle_id=self.cycle_id).delete()
        except (FieldDoesNotExist, KeyError, ValueError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except AttributeError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Delete data for cycle - {self.cycle_id} successfully",
            payload={},
        )

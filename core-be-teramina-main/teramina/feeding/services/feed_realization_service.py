# pylint: disable=no-member

from datetime import datetime
import pandas as pd

from mongoengine.errors import LookUpError, InvalidQueryError
from mongoengine import QuerySet

from ..schemas.feed_schema import FeedDataSchema, FeedUpdateSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema
from ...helpers.constant_value import Constant

from ..models.feed_realization_model import FeedRealization
from ...cycle.models.cycle_model import Cycle
from ...cycle_data.models.cycle_data_model import CycleData, ResultData

from ...data_generator.combined_data_generator import CombinedDataGenerator

from ...helpers.database_updater import (
    update_forecast_combined_data_result,
    update_historical_data_result,
    set_last_updated,
)


class FeedRealizationService:
    """Feed Realization Service"""

    def __init__(self, cycle_id: str, max_ration_number=4) -> None:
        self.cycle_id = cycle_id
        self.max_ration_number = max_ration_number

    def __validate_cycle_existed(self):
        cycle = Cycle.objects(id=self.cycle_id).only("start_date").first()
        if not cycle:
            raise ValueError(f"Data from cycle with id {self.cycle_id} doesn't found")
        return cycle

    def __get_doc(self, date: str = None) -> int:
        """get DOC data

        Args:
            date (str, optional): string of datetime format (%m/%d/%Y). Defaults to None.

        Returns:
            int: DOC
        """
        cycle = self.__validate_cycle_existed()
        if date:
            day = (datetime.strptime(date, "%m/%d/%Y") - cycle.start_date).days

            if (day > Constant.MAX_DOC) or day < 0:
                raise ValueError("Date was not in range of cycle")
        else:
            day = (datetime.now() - cycle.start_date).days

        return day + 1

    def __get_filtered_doc(self, end_date: str) -> int:
        """generate the DOC when end or final date defined

        Args:
            end_date (str): string of datetime format (%m/%d/%Y)

        Returns:
            int: DOC
        """
        cycle = self.__validate_cycle_existed()
        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        day = (end_date - cycle.start_date).days
        return day + 1

    def __generate_update_data(self):
        data = CycleData.objects(cycle_id=self.cycle_id).only("result_data").first()
        if data:
            df = pd.DataFrame(data.result_data)
            combined_df = CombinedDataGenerator(self.cycle_id).generate_data(df)
            historical_df = combined_df.query("category == 'historical'")

            update_historical_data_result(self.cycle_id, historical_df)
            if historical_df.shape[0] > 1:
                update_forecast_combined_data_result(self.cycle_id, combined_df)
            # set last update data
            set_last_updated(self.cycle_id)

    def __convert_to_dataframe(self, data: QuerySet) -> pd.DataFrame:
        """converter MongoDB query set to dataframe

        Args:
            data (QuerySet): _description_

        Returns:
            pd.DataFrame: dataframe result
        """
        ndata = [
            {
                "id": str(x.id),
                "doc": x.doc,
                "ration_number": str(x.ration_number),
                "realized": x.feed_given,
                "leftover": x.feed_leftover,
            }
            for x in data
        ]

        return pd.DataFrame(ndata)

    def add_remaining_feed_realization_data(
        self, max_ration_number: int, current_data: list
    ) -> list:
        """generate format for remaining feed data realization.
            The default is should be empty string.

        Args:
            max_ration_number (int): maximum amount of ration in each day
            current_data (list): current data of feed realization

        Returns:
            list: list of feed realization data
        """
        ration = self.__generata_ration_for_empty_feed_data(max_ration_number)
        for j in current_data:
            index = int(j["ration_number"]) - 1
            ration[index] = j

        return ration

    def __generate_feed_ration_format(self, index: tuple, data: dict) -> dict:
        """generate feed ration format

        Args:
            index (tuple): tuple of (doc, ration_number)
            data (dict): dictionaries aggregate of ration data
                        ```
                        {
                            (<doc>, <ration_number>) : {
                                "id": <id>,
                                "realizaed": <feed realization>,
                                "leftover": <feed left over>
                            }
                        }
                        ```

        Returns:
            dict: formatter data
        """

        result = {
            "title": f"Ration {index[1]}",
            "ration_number": str(index[1]),
            "id": data[index]["id"],
            "value": [
                {"title": "Realization", "value": data[index]["realized"], "unit": "m"},
                {"title": "Leftover", "value": data[index]["leftover"], "unit": "m"},
            ],
        }

        return result

    def parse_daily_feed_data(self, data: dict) -> list:
        """parsing the daily feed data that exported from dataframe before.

        Args:
            data (dict): dictionaries aggregate of ration data
                    ```
                    {
                        (<doc>, <ration_number>) : {
                            "id": <id>,
                            "realizaed": <feed realization>,
                            "leftover": <feed left over>
                        }
                    }
                    ```

        Returns:
            list: parse data with specific format
        """

        index = data.keys()
        result = []
        current_doc = None
        ration = []

        for idx, i in enumerate(index):
            ration.append(self.__generate_feed_ration_format(i, data))
            if (current_doc != i[0]) or (idx == (len(index) - 1)):
                if idx != 0:
                    ration = self.add_remaining_feed_realization_data(self.max_ration_number, ration)
                    result.append({"doc": current_doc, "ration": ration})
                    ration = []

                current_doc = i[0]

            if len(index) == 1:
                current_doc = i[0]
                ration = self.add_remaining_feed_realization_data(self.max_ration_number, ration)
                result.append({"doc": current_doc, "ration": ration})

        return result

    def __ration_validation(self, ration_number):
        if ration_number > self.max_ration_number:
            raise ValueError(
                f"Too many ratios. Only lower than {self.max_ration_number} allowed."
            )

        if ration_number < 1:
            raise ValueError("The minimal ratio number allowed is 1")

    def __update_fr_cycle_data(self, current_doc):
        feed_realization = (
            FeedRealization.objects(cycle_id=self.cycle_id, doc=current_doc)
            .only("feed_ration")
            .all()
        )
        if feed_realization:
            feed_realization1 = [i.feed_ration for i in feed_realization]
            feed_ration = sum(feed_realization1)

            data = CycleData.objects(cycle_id=self.cycle_id).only("result_data").first()
            if data:
                df = pd.DataFrame(data.result_data)
                df.loc[df["doc"] == current_doc, "fr"] = feed_ration
                data.result_data = df.to_dict("records")
                data.save()

    def add_feed_data(self, data: FeedDataSchema):
        """add feed data function"""
        try:
            self.__ration_validation(data.ration_number)
            current_doc = self.__get_doc(data.date)

            result_data = (
                ResultData.objects(cycle_id=self.cycle_id).only("result_data").first()
            )
            if not result_data:
                raise ValueError("Data not found.")

            df = pd.DataFrame(result_data.result_data)
            current_biomass = df.loc[current_doc - 1, "biomass_kg"]
            if current_biomass == 0:
                current_biomass = df.loc[current_doc - 1, "harvest_biomass_kg"]

            # query the feed realization
            current_ration = (
                FeedRealization.objects(
                    cycle_id=self.cycle_id,
                    doc=current_doc,
                    ration_number=data.ration_number,
                )
                .only("id")
                .first()
            )

            # ensure that the data doesn't exist
            if not current_ration:
                feed_ration = data.feed_given / current_biomass * 100
                feed = FeedRealization(
                    cycle_id=self.cycle_id,
                    doc=current_doc,
                    ration_number=data.ration_number,
                    feed_given=data.feed_given,
                    feed_ration=feed_ration,
                    feed_leftover=data.feed_leftover,
                )

                feed.save()

                ## update Cycle's Data
                self.__update_fr_cycle_data(current_doc)
                self.__generate_update_data()

            else:
                raise ValueError(
                    f"Feed ration {data.ration_number} at doc {current_doc} already exist"
                )

        except (LookUpError, InvalidQueryError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except (ValueError, KeyError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Adding feed data for cycle with id - {self.cycle_id} success",
            payload={"ration_id": str(feed.id)},
        )

    def edit_feed_data(self, ration_id, data: FeedUpdateSchema):
        """edit feed data function"""
        try:
            result_data = (
                ResultData.objects(cycle_id=self.cycle_id).only("result_data").first()
            )

            if not result_data:
                raise ValueError("Data not found.")
            df = pd.DataFrame(result_data.result_data)

            current_doc = FeedRealization.objects(id=str(ration_id)).only("doc").first()
            current_doc = current_doc.doc

            current_biomass = df.loc[current_doc - 1, "biomass_kg"]
            if current_biomass == 0:
                current_biomass = df.loc[current_doc - 1, "harvest_biomass_kg"]

            feed_ration = data.feed_given / current_biomass * 100
            FeedRealization.objects(id=str(ration_id)).update(
                set__feed_given=data.feed_given,
                set__feed_ration=feed_ration,
                set__feed_leftover=data.feed_leftover,
            )

            ## update Cycle's Data
            self.__update_fr_cycle_data(current_doc)
            self.__generate_update_data()

        except (LookUpError, InvalidQueryError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except (ValueError, KeyError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message=f"Update feed data for ration with id - {ration_id} success",
            payload=data,
        )

    def __generata_ration_for_empty_feed_data(self, number_of_ration: int) -> list:
        ration = [
            {
                "title": f"Ration {i + 1}",
                "ration_number": str(i + 1),
                "id": "",
                "value": [
                    {"title": "Realization", "value": "", "unit": "m"},
                    {"title": "Leftover", "value": "", "unit": "m"},
                ],
            }
            for i in range(number_of_ration)
        ]

        return ration

    def get_list_feed_data(
        self, end_date: str = None, number_of_ration: int = 4
    ) -> list:
        """Get the list of feed data

        Args:
            end_date (str, optional): datetime format (%m/%d/%Y). Defaults to None.
            number_of_ration (int, optional): the number of ration in each day. Defaults to 4.

        Returns:
            list: list of formated data feed ration
        """
        if not end_date:
            doc = self.__get_doc(datetime.strftime(datetime.now(), "%m/%d/%Y"))
            feed_data = FeedRealization.objects(cycle_id=self.cycle_id).all()
        else:
            doc = self.__get_filtered_doc(end_date)
            feed_data = FeedRealization.objects(cycle_id=self.cycle_id, doc=doc).all()

        if feed_data:
            df = self.__convert_to_dataframe(feed_data)
            df["ration_number"] = df["ration_number"].astype(str)
            data = df.groupby(["doc", "ration_number"]).min().to_dict("index")
            result_data = self.parse_daily_feed_data(data)

            feed_given = [i.feed_given for i in feed_data]
            feed_given = sum(feed_given)
            result_data[0]["feed_given"] = f"{feed_given:,.0f} Kg"
        else:
            ration = self.__generata_ration_for_empty_feed_data(number_of_ration)
            total_feed_given = "0.0 Kg"
            result_data = [
                {"doc": doc, "ration": ration, "feed_given": total_feed_given}
            ]

        return result_data

    def get_feed_data(self, end_date: str = None, number_of_ration: int = 4):
        """get feed data

        Args:
            end_date (str, optional): last filtered date. Defaults to None.
            number_of_ration (int, optional): number of ration. Defaults to 4.
        """
        try:
            feed_data = self.get_list_feed_data(end_date, number_of_ration)
        except (ValueError, KeyError, IndexError, AttributeError) as e:
            return 400, DataErrorSchema(code=400, message=str(e))

        return 200, DataSuccessSchema(
            code=200, message="success", payload={"data": feed_data}
        )

    def reset_all_feed(self):
        """reset feed data"""
        try:
            FeedRealization.objects(cycle_id=self.cycle_id).delete()

        except (ValueError, KeyError, IndexError, AttributeError) as e:
            return 400, DataErrorSchema(code=400, message=str(e))

        return 200, DataSuccessSchema(code=200, message="success", payload={})

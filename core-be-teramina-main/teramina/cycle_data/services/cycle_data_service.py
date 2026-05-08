# pylint: disable=E1137
import hashlib
import pandas as pd
import numpy as np
from mongoengine.errors import InvalidQueryError, FieldDoesNotExist

from ...helpers.constant_column import Column
from ...helpers.data_preprocessor import waterquality_columns_checker
from ...schemas.general_schema import DataSuccessSchema, DataErrorSchema

from ..models.cycle_data_model import CycleData, ResultData
from ..models.upload_log_model import DataUploadLog
from ...farm.models.farm_model import Farm
from ...pond.models.pond_model import Pond
from ...cycle.models.cycle_model import Cycle
from ...user.models.user_model import User

from ...data_generator.combined_data_generator import CombinedDataGenerator

from ...helpers.database_updater import (
    update_historical_data_result,
    update_forecast_combined_data_result,
    set_last_updated,
)

from ...helpers.data_preprocessor import (
    cost_data_preprocessing,
    sr_data_preprocessing,
    smart_impute,
    detect_gap_windows,
)
from .data_validator import validate_cycle_data
from ...helpers.farm_data_collecting import combine_with_df

from ...helpers.pinecone_data_indexing import PineconeIndexing

def get_list_data_main(user_id: str=None, farm_id=None, pond_id=None):
    """get list of main data"""
    if not farm_id and not pond_id:
        data = Farm.objects.all() if not user_id else Farm.objects(user_id=user_id).all()
    elif farm_id and not pond_id:
        data = Pond.objects(farm_id=farm_id).all()
    elif not farm_id and pond_id:
        raise ValueError("farm_id should be not None, if pond_id is not None")
    else:
        data = Cycle.objects(pond_id=pond_id).all()

    data = [i.to_dict() for i in data]
    return data


class CycleService:
    """Farming data service that leads to add/update and view the data"""

    def __parse_data_csv(self, path_file: str) -> pd.DataFrame:
        """parse data from csv

        Args:
            path_file (str): path file of the CSV file

        Raises:
            KeyError: Raise up when required columns are not found.

        Returns:
            pd.DataFrame: Dataframe of the uploaded data
        """
        df = pd.read_csv(path_file, sep=",")
        df = self.__completing_data(df)
        try:
            added_columns = []
            if "feed_given" in df.columns:
                added_columns.append("feed_given")
                if "seed_cost" in df.columns:
                    added_columns.append("seed_cost")
                df["fr"] = None
            elif "seed_cost" in df.columns:
                added_columns.append("seed_cost")

            wq_columns = waterquality_columns_checker(df.columns.tolist())
            # get sampling column
            sampling_columns = df.filter(like="sampling_").columns.tolist()
            df = df[Column.required_columns + added_columns + wq_columns + sampling_columns]

        except KeyError as exc:
            raise KeyError(
                f"Missing required columns. Required columns are -> {Column.required_columns}"
            ) from exc

        return df

    def __parse_data_xlsx(self, path_file: str) -> pd.DataFrame:
        """parse data from xlsx

        Args:
            path_file (str): path file of the CSV file

        Returns:
            pd.DataFrame: Dataframe of the uploaded data
        """
        try:
            df = pd.read_excel(path_file, sheet_name="daily_data")

            df = self.__completing_data(df)

            columns = set(df.columns)
            cost_set = set(Column.cost_columns)

            if "feed_given" in columns:
                df = df[Column.required_columns_simple + ["feed_given"]]
            else:
                df = df[Column.required_columns_simple]

            if not cost_set.issubset(columns):
                cost_spending = pd.read_excel(path_file, sheet_name="cost_spending")
                cost_item = pd.read_excel(path_file, sheet_name="cost_item")

                cost_df = cost_data_preprocessing(cost_item, cost_spending)
                df = pd.concat([df, cost_df], axis=1)
            else:
                raise KeyError("Missing required columns")

        except KeyError as exc:
            raise KeyError("Missing required columns") from exc
        except ValueError as exc:
            raise ValueError("Required sheet name not found") from exc

        return df

    def __validate_data(self, df: pd.DataFrame, start_date):
        # abw value validation
        if (df["abw"] <= 0).any():
            raise ValueError(
                "Invalid input detected: Average body weight values should be positive."
            )

        # DO=0 hard reject: causes ZeroDivisionError in feeding risk formula
        if "do" in df.columns and (df["do"] == 0).any():
            bad_docs = df.loc[df["do"] == 0, "doc"].tolist()
            raise ValueError(
                f"Invalid input detected: DO (dissolved oxygen) is zero on DOC(s) {bad_docs}. "
                "Check sensor readings — DO=0 indicates a sensor fault or severe hypoxia event."
            )

        # date range value validation
        date_range = (df["date"].loc[0] - start_date).days
        if date_range != 0:
            raise ValueError(
                "Your cycle began on a different day than what the data file says."
            )

    def __completing_data(self, df: pd.DataFrame):
        df["doc"] = df["doc"].astype(int)
        # data completion
        complete_df = pd.DataFrame({"doc": range(1, df["doc"].iat[-1] + 1)})
        df = complete_df.merge(df, on="doc", how="left")

        # set the date
        df["date"] = pd.to_datetime(df["date"])
        if df["date"].isna().any():
            first_valid_datetime = df["date"].first_valid_index()
            initial_date = df.loc[first_valid_datetime, "date"] - pd.Timedelta(
                days=int(first_valid_datetime)
            )
            df["date"] = pd.date_range(
                start=initial_date, periods=df.shape[0], freq="D"
            )

        # Detect missing sensor values and store summary for the API response
        sensor_cols = ["temperature", "do", "nh3", "sr", "initial_stocking"]
        self._missing_sensor_summary = {
            col: int(df[col].isna().sum())
            for col in sensor_cols
            if df[col].isna().any()
        }

        # Detect long gaps (> 3 consecutive days) for reporting
        self._gap_windows = detect_gap_windows(df, sensor_cols + ["abw"])

        # Apply field-specific imputation (ffill for DO/temp/NH3, interp for ABW, etc.)
        # SR is excluded here — handled by sr_data_preprocessing below
        df = smart_impute(df)

        # validate the sr values (normalize, interpolate gaps, enforce cummin)
        df = sr_data_preprocessing(df)

        # define the columns data
        cols = df.columns

        if "protein_content" not in cols:
            df["protein_content"] = 36

        if "chb" not in cols:
            df["chb"] = 72

        df["w0"] = df["abw"].iat[0] if not np.isnan(df["abw"].iat[0]) else 0.01

        required_cost_columns = Column.cost_columns
        cost_columns = [col for col in required_cost_columns if col not in cols]
        df.loc[:, cost_columns] = 0

        df[required_cost_columns] = df[required_cost_columns].fillna(0)
        return df

    def add_cycle_data(self, cycle_id, file, user_id, source_type="csv"):
        """add/update farming data

        Args:
            cycle_id (str): id of a cycle
            file (object): file's object
            user_id (str): id of a user that uploaded the data
            source_type (str, optional): extension of file that uploaded. Defaults to "csv".
        """

        self._missing_sensor_summary = {}
        self._gap_windows = {}
        self._validation_report = None
        try:
            cycle = Cycle.objects(id=str(cycle_id)).only("start_date").first()
            start_date = cycle.start_date

            if source_type == "csv":
                df = self.__parse_data_csv(file)
            else:
                df = self.__parse_data_xlsx(file)

            # structural validation (abw, date range, DO=0)
            self.__validate_data(df, start_date)

            # physiological bounds validation
            validation_report = validate_cycle_data(df)
            self._validation_report = validation_report
            if validation_report.has_hard_failures():
                failures = validation_report.to_dict()["hard_failures"]
                detail = "; ".join(f["reason"] for f in failures[:5])
                DataUploadLog(
                    cycle_id=str(cycle_id),
                    user_id=str(user_id),
                    source_type=source_type,
                    status="failed",
                    row_count=len(df),
                    doc_min=int(df["doc"].min()) if "doc" in df.columns else 0,
                    doc_max=int(df["doc"].max()) if "doc" in df.columns else 0,
                    hard_failures=failures,
                    warnings=validation_report.to_dict()["warnings"],
                    imputed_summary=self._missing_sensor_summary,
                    gap_windows=self._gap_windows,
                ).save()
                return 400, DataErrorSchema(
                    code=400,
                    message=f"Data contains physiologically invalid values: {detail}",
                )

            # add cycle id
            df.loc[:, "cycle_id"] = cycle_id

            # Run pipeline BEFORE saving — if it crashes, MongoDB state is unchanged
            combined_df = CombinedDataGenerator(cycle_id).generate_data(df)

            historical_df = combined_df.query("category == 'historical'").reset_index(
                drop=True
            )

            # Pipeline succeeded — persist raw data and derived results
            CycleData.objects(cycle_id=cycle_id).update_one(
                set__result_data=df.to_dict("records"),
                upsert=True,
            )
            update_historical_data_result(cycle_id, historical_df)

            # indexing and store to gcs
            historical_df = combine_with_df(cycle_id=cycle_id, df=historical_df)


            cycle = Cycle.objects(id=cycle_id).first()
            try:
                if cycle.vector_list:
                    vector_ids = PineconeIndexing(user_id).update_index(
                        ids=cycle.vector_list, df=historical_df
                    )
                else:
                    vector_ids = PineconeIndexing(user_id).create_index(
                        df=historical_df
                    )

                cycle.vector_list = vector_ids
                cycle.save()
            except FieldDoesNotExist:
                vector_ids = PineconeIndexing(user_id).create_index(df=historical_df)

            cycle.vector_list = vector_ids
            cycle.save()

            if historical_df.shape[0] > 1:
                update_forecast_combined_data_result(cycle_id, combined_df)

            # set last update data
            set_last_updated(cycle_id)

            User.objects(id=user_id).update(set__is_there_data=True)

        except (
            IndexError,
            KeyError,
            AttributeError,
            ValueError,
            TypeError,
        ) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except ZeroDivisionError:
            return 400, DataErrorSchema(
                code=400, message="It's possible that DO levels contain zeros."
            )

        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except InvalidQueryError:
            return 400, DataErrorSchema(code=400, message="Insert values error")

        vr = self._validation_report
        vr_dict = vr.to_dict() if vr else {"hard_failures": [], "warnings": []}

        snapshot_hash = hashlib.md5(
            pd.util.hash_pandas_object(df, index=True).values.tobytes()
        ).hexdigest()

        DataUploadLog(
            cycle_id=str(cycle_id),
            user_id=str(user_id),
            source_type=source_type,
            status="success",
            row_count=len(df),
            doc_min=int(df["doc"].min()) if "doc" in df.columns else 0,
            doc_max=int(df["doc"].max()) if "doc" in df.columns else 0,
            hard_failures=[],
            warnings=vr_dict["warnings"],
            imputed_summary=self._missing_sensor_summary,
            gap_windows=self._gap_windows,
            snapshot_hash=snapshot_hash,
        ).save()

        payload = {
            "status": "ok",
            "cycle_id": str(cycle_id),
            "validation": {
                "warnings": vr_dict["warnings"],
                "imputed_summary": self._missing_sensor_summary,
                "gap_windows": self._gap_windows,
            },
        }

        return 200, DataSuccessSchema(
            code=200,
            message="Add Data to a cycle success",
            payload=payload,
        )

    def get_cycle_data(self, cycle_id):
        """view the farming data

        Args:
            cycle_id (str): id of a cycle

        """
        try:
            data = ResultData.objects(cycle_id=cycle_id).first()
            if data:
                df = pd.DataFrame(data.result_data)
                columns = list(df.columns)
                df = df.replace({np.nan: None})
                result_data = df.to_dict("records")
            else:
                result_data = []
                columns = []

            cycle = (
                Cycle.objects(id=str(cycle_id))
                .only("name", "start_date", "pond_id")
                .first()
            )
            pond = Pond.objects(id=str(cycle.pond_id)).only("name", "farm_id").first()
            farm = Farm.objects(id=str(pond.farm_id)).only("name").first()

        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except (IndexError, KeyError, AttributeError, ValueError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Loaded data successfully",
            payload={
                "farm_name": farm.name,
                "pond_name": pond.name,
                "cycle_name": cycle.name,
                "cycle_start_date": cycle.start_date,
                "columns": columns,
                "data": result_data,
            },
        )

    def get_cycle_dataframe(self, cycle_id):
        """get dataframe"""
        data = ResultData.objects(cycle_id=cycle_id).first()
        if data:
            df = pd.DataFrame(data.result_data)
            df = df.replace({np.nan: None})
        else:
            df = pd.DataFrame()

        return df

    def get_cycle_dataframe_by_filter(self, email: str, farm_id = None):
        """get dataframe"""
        user = User.objects(email=email).first()
        if not user:
            raise ValueError("Email not found")

        if not farm_id:
            farm_data = get_list_data_main(user_id=str(user.id))
        else:
            selected_farm = Farm.objects(id=farm_id).first()
            farm_data = [{"id": farm_id, "name": selected_farm.name}]

        list_df = []
        for farm in farm_data:
            pond_data = get_list_data_main(farm_id=farm["id"])
            for pond in pond_data:
                cycle_data = get_list_data_main(
                    farm_id=str(pond["farm_id"]), pond_id=str(pond["id"])
                )
                for cycle in cycle_data:
                    data = ResultData.objects(cycle_id=str(cycle["id"])).first()
                    if data:
                        df = pd.DataFrame(data.result_data)
                        df = df.replace({np.nan: None})
                        df["pond_id"] = str(pond["id"])
                        df["pond_name"] = str(pond["name"])
                        df["farm_id"] = str(pond["farm_id"])
                        df["farm_name"] = str(farm["name"])

                list_df.append(df)

        return pd.concat(list_df)

    def get_last_data(self, cycle_id):
        """get cycle data"""
        try:
            df = self.get_cycle_dataframe(cycle_id)
            data = df.iloc[-5:].to_dict("records")
        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))
        except (IndexError, KeyError, AttributeError, ValueError) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="Loaded data successfully",
            payload={"data": data}
        )

import pandas as pd
# import numpy as np
from mongoengine.errors import DoesNotExist, FieldDoesNotExist
from teramina.farm.models.farm_model import Farm
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from teramina.cost_data.models.cost_data_model import CostData
from teramina.cost_data.lib.mapper import generate_pl_report

class CostDataService:
    """CostDataService
    
    cost data service are services that help to manage the cost data
    """
    def __init__(self, cycle_id):
        self.cycle_id = cycle_id

    def data_validation(self, category: str, df: pd.DataFrame):
        """data validation"""
        if category == "energy":
            cols = ["date", "hp"]
        elif category == "operation":
            cols = ["date", "feed_cost", "probiotic_cost"]
        else:
            cols = ["date", "bonuss_cost", "hp"]

        if not set(df.columns).intersection(set(cols)):
            raise ValueError(
                f"Please make sure your {category} data contains the required columns: {cols}"
            )

    def add_data(self, labels, files):
        """add a new data"""
        if len(labels) != len(files):
            raise ValueError("please make sure your label defined correctly")
        for _, j in zip(labels,files):
            df = pd.read_csv(j)
            # self.data_validation(i, df)

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload=df.iloc[10].to_dict()
        )

    @staticmethod
    def add_single_data(farm_id, start_date, end_date, file) -> pd.DataFrame:
        """this is temporary function"""
        # df = pd.read_csv(file)
        try:
            df = pd.read_excel(file, sheet_name="data")
            current_data = CostData.objects(farm_id=farm_id).first()
            if current_data:
                current_data.start_date = start_date
                current_data.end_date = end_date
                current_data.data = df.to_dict("records")
                current_data.save()
            else:
                CostData(
                    farm_id=farm_id,
                    start_date=start_date,
                    end_date=end_date,
                    data=df.to_dict("records")
                ).save()
        except( DoesNotExist, FieldDoesNotExist) as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={}
        )

    @staticmethod
    def download_single_data(farm_id):
        """this is temporary function"""

        cost_data = CostData.objects(farm_id=farm_id).first()
        if not cost_data:
            raise ValueError("Cost data is not found")

        farm = Farm.objects(id=farm_id).first()
        if not farm:
            raise ValueError("Farm is not found")

        df = pd.DataFrame(cost_data.data)
        work_book = generate_pl_report(farm.name, cost_data.start_date, cost_data.end_date, df)
        return work_book

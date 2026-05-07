# pylint: disable=too-few-public-methods, E0401, C0115, E0402
from ninja import Schema
from mongoengine.errors import InvalidQueryError, FieldDoesNotExist
from ...schemas.general_schema import DataSuccessSchema, DataErrorSchema
from ..models.variable_model import WQVariable


class AddVariableSchema(Schema):
    name: str
    weight: float
    type: str
    lower_bound: float = None  # Set default to None (null)
    optimal_min: float = None  # Set default to None (null)
    optimal_max: float = None  # Set default to None (null)
    upper_bound: float = None  # Set default to None (null)


class VariableManagement:
    """Water Quality variable management"""

    def is_variable_exist(self, name: str):
        """is variable exist checker"""
        data = WQVariable.objects(name=name).first()
        return data

    def add_variable(self, data: AddVariableSchema):
        """update new wq variables"""
        try:
            var_data = self.is_variable_exist(data.name)
            if var_data:
                var_data.weight = data.weight
                var_data.type = data.type
                var_data.lower_bound = data.lower_bound
                var_data.optimal_min = data.optimal_min
                var_data.optimal_max = data.optimal_max
                var_data.upper_bound = data.upper_bound
            else:
                var_data = WQVariable(
                    name=data.name,
                    weight=data.weight,
                    type=data.type,
                    lower_bound=data.lower_bound,
                    optimal_min=data.optimal_min,
                    optimal_max=data.optimal_max,
                    upper_bound=data.upper_bound,
                )

            var_data.save()
            return 200, DataSuccessSchema(
                code=200, message="Variable successfully registered.", payload={}
            )

        except InvalidQueryError:
            return 400, DataErrorSchema(
                code=400, message="Failed to add/update data due to a query error"
            )

    def get_variable_names(self):
        """get variable names"""
        data = WQVariable.objects.all()
        data = [i.name for i in data]
        return data

    def get_water_quality_vars(self):
        """get water quality variables variables"""

        try:
            data = self.get_variable_names()
        except InvalidQueryError:
            return 400, DataErrorSchema(code=400, message="Failed to load data")

        except FieldDoesNotExist:
            return 400, DataErrorSchema(code=400, message="Failed to load data")

        return 200, DataSuccessSchema(
            code=200,
            message="Variable successfully registered.",
            payload={"data": data},
        )

    def get_water_quality_var(self, var_name):
        """get water quality variable"""

        try:
            data = self.is_variable_exist(var_name)
            data = {
                "name": data.name,
                "weight": data.weight,
                "type": data.type,
                "lower_bound": data.lower_bound,
                "optimal_min": data.optimal_min,
                "optimal_max": data.optimal_max,
                "upperd_bound": data.upper_bound,
            }
        except InvalidQueryError:
            return 400, DataErrorSchema(code=400, message="Failed to load data")

        except FieldDoesNotExist:
            return 400, DataErrorSchema(code=400, message="Failed to load data")

        return 200, DataSuccessSchema(
            code=200,
            message="Variable successfully registered.",
            payload={"data": data},
        )

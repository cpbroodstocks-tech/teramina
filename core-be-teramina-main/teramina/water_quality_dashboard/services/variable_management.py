# pylint: disable=too-few-public-methods, E0401, C0115, E0402
from ninja import Schema
from mongoengine.errors import InvalidQueryError, FieldDoesNotExist
from ...schemas.general_schema import DataSuccessSchema, DataErrorSchema
from ..models.variable_model import WQVariable


DEFAULT_WQ_VARIABLES = [
    dict(
        name="temperature", weight=0.15, type="float",
        lower_bound=23, optimal_min=27, optimal_max=30, upper_bound=33,
    ),
    dict(
        name="do", weight=0.25, type="float",
        lower_bound=2, optimal_min=3.5, optimal_max=9, upper_bound=10,
    ),
    dict(
        name="nh3", weight=0.20, type="float",
        lower_bound=0, optimal_min=0, optimal_max=0.25, upper_bound=2.09,
    ),
    dict(
        name="ph", weight=0.15, type="float",
        lower_bound=6.5, optimal_min=7.5, optimal_max=8.5, upper_bound=9,
    ),
    dict(
        name="alkalinity", weight=0.10, type="float",
        lower_bound=50, optimal_min=100, optimal_max=200, upper_bound=300,
    ),
    dict(
        name="salinity", weight=0.10, type="float",
        lower_bound=5, optimal_min=10, optimal_max=25, upper_bound=35,
    ),
    dict(
        name="tss", weight=0.05, type="float",
        lower_bound=0, optimal_min=0, optimal_max=100, upper_bound=300,
    ),
]
DISPLAY_WQ_VARIABLES = {"temperature", "do", "nh3", "ph", "salinity", "turbidity"}
WQ_VARIABLE_ALIASES = {"temp": "temperature"}


def canonical_wq_variable_name(column_name):
    """Return the configured water-quality variable represented by a data column."""
    base_name = column_name.split("_", 1)[0]
    return WQ_VARIABLE_ALIASES.get(base_name, base_name)


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

    def get_display_variable_names(self):
        """Return configured variables plus supported non-indexed readings."""
        return set(self.get_variable_names()).union(DISPLAY_WQ_VARIABLES)

    def ensure_default_variables(self):
        """Create missing baseline variables without overwriting configured values."""
        for values in DEFAULT_WQ_VARIABLES:
            if not self.is_variable_exist(values["name"]):
                WQVariable(**values).save()

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

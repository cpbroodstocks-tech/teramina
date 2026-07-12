# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema
from pydantic import ConfigDict


class CreateCycleSchema(Schema):
    name: str
    start_date: str

    model_config = ConfigDict(json_schema_extra={
            "name": "Create Cycle",
            "example": {"name": "A", "start_date": "mm/dd/yyyy"},
        })


class UpdateCycleSchema(Schema):
    name: str
    start_date: str
    is_active: bool

    model_config = ConfigDict(json_schema_extra={
            "name": "Create Cycle",
            "example": {"name": "A", "start_date": "mm/dd/yyyy", "is_active": False},
        })

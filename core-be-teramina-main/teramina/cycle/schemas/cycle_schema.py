# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class CreateCycleSchema(Schema):
    name: str
    start_date: str

    class Config:
        schema_extra = {
            "name": "Create Cycle",
            "example": {"name": "A", "start_date": "mm/dd/yyyy"},
        }


class UpdateCycleSchema(Schema):
    name: str
    start_date: str
    is_active: bool

    class Config:
        schema_extra = {
            "name": "Create Cycle",
            "example": {"name": "A", "start_date": "mm/dd/yyyy", "is_active": False},
        }

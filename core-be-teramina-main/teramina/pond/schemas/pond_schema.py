# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class PondDataSchema(Schema):
    name: str
    size: float
    pond_construction: str
    pond_shape: str

    class Config:
        schema_extra = {
            "name": "Add Pond",
            "example": {
                "name": "A",
                "size": 2000.0,
                "pond_construction": "HDPE",
                "pond_shape": "Persegi",
            },
        }


class UpdatePondSchema(Schema):
    name: str
    size: float
    pond_construction: str
    pond_shape: str
    is_active: bool

    class Config:
        schema_extra = {
            "name": "Update Pond",
            "example": {
                "name": "A",
                "size": 2000.0,
                "pond_construction": "HDPE",
                "pond_shape": "Persegi",
                "is_active": False,
            },
        }

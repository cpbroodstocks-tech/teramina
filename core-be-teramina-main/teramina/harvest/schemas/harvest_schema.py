# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class HarvestDataSchema(Schema):
    partial1: dict
    partial2: dict
    partial3: dict
    final: dict

    class Config:
        schema_extra = {
            "name": "Harvest Data",
            "example": {
                "partial1": {"doc": 60, "biomass": 120, "revenue": 10000000},
                "partial2": {"doc": 80, "biomass": 1000, "revenue": 10000000},
                "partial3": {"doc": 90, "biomass": 890, "revenue": 10000000},
                "final": {"doc": 100, "biomass": 1200, "revenue": 10000000},
            },
        }

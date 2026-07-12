# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema
from pydantic import ConfigDict


class FarmDataSchema(Schema):
    name: str
    location: str

    model_config = ConfigDict(json_schema_extra={
            "name": "Farm Data",
            "example": {
                "name": "Tambak Wonosari",
                "location": "Desa Wringinputih, Kecamatan Muncar, Kab Banyuwangi, Jawa Timur",
            },
        })

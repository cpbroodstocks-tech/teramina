# pylint: disable=missing-class-docstring, too-few-public-methods

from ninja import Schema


class FarmDataSchema(Schema):
    name: str
    location: str

    class Config:
        schema_extra = {
            "name": "Farm Data",
            "example": {
                "name": "Tambak Wonosari",
                "location": "Desa Wringinputih, Kecamatan Muncar, Kab Banyuwangi, Jawa Timur",
            },
        }

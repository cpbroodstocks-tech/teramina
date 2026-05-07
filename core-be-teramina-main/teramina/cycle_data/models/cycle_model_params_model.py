# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class CycleModelParams(Document):
    """Per-cycle fitted growth model parameters replacing global alpha constants."""
    cycle_id = fields.StringField(required=True, unique=True)
    alpha1 = fields.FloatField()
    alpha2 = fields.FloatField()
    alpha3 = fields.FloatField()
    alpha4 = fields.FloatField()
    r_squared = fields.FloatField()       # goodness of fit, 0–1
    fitted_at_doc = fields.IntField()     # DOC when last fitted
    sample_count = fields.IntField()      # number of ABW points used
    model_version = fields.StringField(default="adaptive_v1")
    last_updated = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["cycle_id"],
        "collection": "cycle_model_params",
    }

    objects = QuerySetManager()

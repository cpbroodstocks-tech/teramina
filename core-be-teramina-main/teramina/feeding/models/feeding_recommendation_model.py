# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class FeedingRecommendation(Document):
    """Stores daily feeding recommendations per cycle+DOC."""
    cycle_id = fields.StringField(required=True)
    doc = fields.IntField(required=True)
    recommended_ration_kg = fields.FloatField()
    recommended_frequency = fields.IntField()         # times per day
    ration_per_feeding = fields.ListField()           # kg per each feeding slot
    adjustment_reason = fields.StringField(default="")
    model_layer = fields.StringField(default="rule_v1")  # "blind_feed"|"rule_v1"|"ml_v1"
    model_version = fields.StringField(default="1.0")
    features_used = fields.DictField()               # snapshot of inputs used
    confidence = fields.FloatField(default=1.0)
    created_at = fields.DateTimeField(default=datetime.now)
    last_updated = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["cycle_id", "doc"],
        "collection": "feeding_recommendations",
    }
    objects = QuerySetManager()


class FeedingOverride(Document):
    """Records when a farmer overrides a recommendation — used as training signal."""
    cycle_id = fields.StringField(required=True)
    doc = fields.IntField(required=True)
    recommended_kg = fields.FloatField()
    actual_kg = fields.FloatField()
    override_reason = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["cycle_id"],
        "collection": "feeding_overrides",
    }
    objects = QuerySetManager()

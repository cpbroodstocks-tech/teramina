# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class CycleInsightCache(Document):
    """Cached structured insight for a cycle at a specific DOC."""
    cycle_id = fields.StringField(required=True)
    insight_type = fields.StringField(required=True)  # "performance"|"water_quality"|"feeding"|"harvest"|"weekly"
    doc_at_generation = fields.IntField()
    insight_data = fields.DictField()   # full structured insight JSON
    generated_at = fields.DateTimeField(default=datetime.now)
    model_used = fields.StringField()

    meta = {
        "indexes": ["cycle_id", "insight_type"],
        "collection": "cycle_insight_cache",
    }
    objects = QuerySetManager()

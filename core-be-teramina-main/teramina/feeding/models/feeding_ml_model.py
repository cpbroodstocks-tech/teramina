# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class FeedingModelArtifact(Document):
    """Stores trained XGBoost model binary in MongoDB."""
    version = fields.StringField(required=True, unique=True)
    model_bytes = fields.BinaryField()
    feature_names = fields.ListField(fields.StringField())
    metrics = fields.DictField()        # rmse, mae, r2, n_samples, n_cycles
    trained_at = fields.DateTimeField(default=datetime.utcnow)
    is_active = fields.BooleanField(default=False)

    meta = {
        "indexes": ["version", "is_active"],
        "collection": "feeding_model_artifacts",
    }
    objects = QuerySetManager()

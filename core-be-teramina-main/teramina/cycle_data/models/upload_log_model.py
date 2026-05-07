# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class DataUploadLog(Document):
    """Audit trail for every cycle data upload attempt.

    Saved on both success and hard-failure so operators can review
    what was ingested, what was flagged, and how gaps were handled.
    """

    cycle_id = fields.StringField(required=True)
    user_id = fields.StringField(required=True)
    uploaded_at = fields.DateTimeField(default=datetime.utcnow)
    source_type = fields.StringField(choices=["csv", "xlsx"], default="csv")
    status = fields.StringField(choices=["success", "failed"], required=True)

    # shape
    row_count = fields.IntField(default=0)
    doc_min = fields.IntField(default=0)
    doc_max = fields.IntField(default=0)

    # validation results
    hard_failures = fields.ListField(fields.DictField(), default=list)
    warnings = fields.ListField(fields.DictField(), default=list)

    # imputation summary: {col: n_rows_imputed}
    imputed_summary = fields.DictField(default=dict)

    # gap windows: {col: [{start_doc, end_doc, length}]}
    gap_windows = fields.DictField(default=dict)

    # snapshot_hash: md5 of raw dataframe for dedup detection
    snapshot_hash = fields.StringField(default="")

    meta = {
        "indexes": ["cycle_id", "user_id", "uploaded_at"],
        "ordering": ["-uploaded_at"],
    }

    objects = QuerySetManager()

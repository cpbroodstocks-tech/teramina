# pylint: disable=missing-class-docstring

from datetime import datetime
from uuid import uuid4
from mongoengine import Document, EmbeddedDocument, fields, QuerySetManager


class TabSummary(EmbeddedDocument):
    tab = fields.StringField(required=True)
    processed = fields.IntField(default=0)
    inserted = fields.IntField(default=0)
    updated = fields.IntField(default=0)
    deleted = fields.IntField(default=0)
    skipped = fields.IntField(default=0)
    rejected = fields.IntField(default=0)
    error = fields.StringField()
    error_category = fields.StringField()


class RejectedRow(EmbeddedDocument):
    tab = fields.StringField(required=True)
    row_number = fields.IntField()
    field = fields.StringField()
    raw_value = fields.StringField()
    reason = fields.StringField()


class SheetSyncLog(Document):
    cycle_id = fields.StringField(required=True)
    sync_id = fields.UUIDField(default=uuid4)
    spreadsheet_id = fields.StringField()
    source_fingerprint = fields.StringField()
    started_at = fields.DateTimeField()
    finished_at = fields.DateTimeField()
    duration_seconds = fields.FloatField()
    rows_per_second = fields.FloatField()
    status = fields.StringField(default="pending")  # "ok" | "partial" | "error"
    error_category = fields.StringField()
    tab_summaries = fields.EmbeddedDocumentListField(TabSummary)
    rejected_rows = fields.EmbeddedDocumentListField(RejectedRow)

    meta = {
        "indexes": ["cycle_id"],
        "ordering": ["-started_at"],
        "collection": "sheet_sync_logs",
    }

    objects = QuerySetManager()

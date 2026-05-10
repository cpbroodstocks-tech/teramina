# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class SheetIntegration(Document):
    cycle_id = fields.StringField(required=True, unique=True)
    user_id = fields.StringField(required=True)
    spreadsheet_id = fields.StringField()
    spreadsheet_url = fields.StringField()
    is_active = fields.BooleanField(default=True)
    last_synced = fields.DateTimeField()
    last_status = fields.StringField(default="pending")  # "ok" | "error" | "partial" | "pending"
    last_error = fields.StringField(default="")
    rows_synced = fields.IntField(default=0)
    last_sync_log_id = fields.UUIDField()
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["cycle_id", "user_id"],
        "collection": "sheet_integrations",
    }

    objects = QuerySetManager()

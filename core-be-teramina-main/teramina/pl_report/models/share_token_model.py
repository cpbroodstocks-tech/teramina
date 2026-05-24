import secrets
from datetime import datetime, timedelta
from mongoengine import Document, fields, QuerySetManager


class PLReportShareToken(Document):
    token = fields.StringField(required=True, unique=True)
    cycle_id = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=datetime.now)
    expires_at = fields.DateTimeField(required=True)

    meta = {
        "indexes": ["token", "cycle_id"],
        "collection": "pl_report_share_tokens",
    }
    objects = QuerySetManager()

    @classmethod
    def create_for_cycle(cls, cycle_id: str, ttl_days: int = 7) -> "PLReportShareToken":
        token = secrets.token_urlsafe(24)
        doc = cls(
            token=token,
            cycle_id=cycle_id,
            expires_at=datetime.now() + timedelta(days=ttl_days),
        )
        doc.save()
        return doc

    def is_valid(self) -> bool:
        return datetime.now() < self.expires_at

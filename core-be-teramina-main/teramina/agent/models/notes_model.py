# pylint: disable=missing-class-docstring

from datetime import datetime
from mongoengine import Document, fields, QuerySetManager


class FarmerNote(Document):
    """Voice or text note recorded by a farmer, optionally transcribed from audio."""
    user_id = fields.StringField(required=True)
    farm_id = fields.StringField(default="")
    pond_id = fields.StringField(default="")
    cycle_id = fields.StringField(default="")
    content = fields.StringField(required=True)
    source = fields.StringField(choices=["voice", "text"], default="text")
    audio_url = fields.StringField(default="")
    language = fields.StringField(default="id")
    tags = fields.ListField(fields.StringField(), default=list)
    saved_to_memory = fields.BooleanField(default=False)
    memory_id = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["user_id", "farm_id", "-created_at"],
        "collection": "farmer_notes",
    }
    objects = QuerySetManager()

from datetime import datetime
from typing import Optional

from ninja import Schema


class ContentItemSchema(Schema):
    title: str
    slug: str
    summary: str = ""
    category: str
    tags: list[str] = []
    language: str = "en"
    variant_group_id: str = ""
    variant_type: str = "master"
    source_content_id: str = ""
    content_type: str = "guide"
    access_level: str = "free"
    body_markdown: str = ""
    file_url: str = ""
    version: str = "1.0"
    status: str = "draft"
    change_note: str = "Initial version"


class ContentItemUpdateSchema(Schema):
    title: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    language: Optional[str] = None
    variant_group_id: Optional[str] = None
    variant_type: Optional[str] = None
    source_content_id: Optional[str] = None
    content_type: Optional[str] = None
    access_level: Optional[str] = None
    body_markdown: Optional[str] = None
    file_url: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    change_note: Optional[str] = None


class ContentWorkflowTransitionSchema(Schema):
    status: str
    review_note: str = ""


class ContentAccessGrantSchema(Schema):
    user_id: str
    content_id: str
    access_source: str = "manual"
    expires_at: Optional[datetime] = None

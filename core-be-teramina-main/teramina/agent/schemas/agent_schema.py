# pylint: disable=missing-class-docstring

from typing import Optional
from pydantic import BaseModel, Field


class PageContextSchema(BaseModel):
    route: Optional[str] = ""
    page_type: Optional[str] = ""
    farm_id: Optional[str] = ""
    pond_id: Optional[str] = ""
    cycle_id: Optional[str] = ""
    filters: dict[str, str] = Field(default_factory=dict)


class ChatMessageSchema(BaseModel):
    message: str
    session_id: Optional[str] = None
    farm_id: Optional[str] = ""
    pond_id: Optional[str] = ""
    cycle_id: Optional[str] = ""
    page_context: Optional[PageContextSchema] = None


class MemoryCreateSchema(BaseModel):
    farm_id: Optional[str] = ""
    memory_type: str = "note"
    content: str
    pond_id: Optional[str] = ""
    cycle_id: Optional[str] = ""
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.7


class MemoryUpdateSchema(BaseModel):
    memory_type: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    confidence: Optional[float] = None


class SummaryRequestSchema(BaseModel):
    question: str
    model: Optional[str] = None


class ExplainSchema(BaseModel):
    farm_id: str
    cycle_id: Optional[str] = ""
    pond_id: Optional[str] = ""

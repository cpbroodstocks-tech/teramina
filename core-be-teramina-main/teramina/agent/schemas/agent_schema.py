# pylint: disable=missing-class-docstring

from typing import Optional
from pydantic import BaseModel, Field


class ChatMessageSchema(BaseModel):
    message: str
    session_id: Optional[str] = None
    farm_id: Optional[str] = ""
    pond_id: Optional[str] = ""
    cycle_id: Optional[str] = ""


class MemoryCreateSchema(BaseModel):
    farm_id: Optional[str] = ""
    memory_type: str = "note"
    content: str
    pond_id: Optional[str] = ""
    cycle_id: Optional[str] = ""
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.7


class ExplainSchema(BaseModel):
    farm_id: str
    cycle_id: Optional[str] = ""
    pond_id: Optional[str] = ""

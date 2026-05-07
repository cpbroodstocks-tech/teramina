# pylint: disable=missing-class-docstring

from typing import Optional
from pydantic import BaseModel


class ChatMessageSchema(BaseModel):
    message: str
    session_id: Optional[str] = None
    farm_id: Optional[str] = ""
    cycle_id: Optional[str] = ""

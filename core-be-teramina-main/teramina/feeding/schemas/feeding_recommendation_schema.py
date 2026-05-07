# pylint: disable=missing-class-docstring

from typing import Optional, List
from pydantic import BaseModel


class FeedingOverrideSchema(BaseModel):
    actual_kg: float
    override_reason: Optional[str] = ""

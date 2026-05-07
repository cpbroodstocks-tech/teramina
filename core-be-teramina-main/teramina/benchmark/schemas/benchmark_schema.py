# pylint: disable=missing-class-docstring

from pydantic import BaseModel
from typing import Optional


class OptInSchema(BaseModel):
    cycle_id: str

# pylint: disable=missing-class-docstring

from pydantic import BaseModel
from typing import Optional


class ConnectSheetSchema(BaseModel):
    spreadsheet_id: str
    cycle_id: str


class SheetStatusSchema(BaseModel):
    cycle_id: str
    spreadsheet_id: Optional[str]
    spreadsheet_url: Optional[str]
    is_active: bool
    last_synced: Optional[str]
    last_status: str
    last_error: str
    rows_synced: int

# pylint: disable=missing-class-docstring

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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


class TabSummarySchema(BaseModel):
    tab: str
    processed: int
    inserted: int
    updated: int
    skipped: int
    rejected: int


class RejectedRowSchema(BaseModel):
    tab: str
    row_number: Optional[int]
    field: Optional[str]
    raw_value: Optional[str]
    reason: Optional[str]


class SheetSyncLogSchema(BaseModel):
    sync_id: str
    cycle_id: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: str
    tab_summaries: list[TabSummarySchema]
    rejected_rows: list[RejectedRowSchema]


class PreviewSyncResult(BaseModel):
    preview_id: str
    expires_at: datetime
    rows_valid: int
    rows_warning: int
    rows_error: int
    tab_summaries: list[TabSummarySchema]
    rejected_rows: list[RejectedRowSchema]

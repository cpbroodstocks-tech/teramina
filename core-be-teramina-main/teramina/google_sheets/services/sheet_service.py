# pylint: disable=broad-except, too-many-branches, too-many-statements, too-many-locals

import logging
import os
import hashlib
import json
import time
from datetime import datetime, date as date_type
from uuid import UUID

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.cycle_data.services.data_validator import validate_cycle_data
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.cost_data.models.cost_data_model import CostData
from teramina.pond.models.pond_model import Pond
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema

from ..models.sheet_integration_model import SheetIntegration
from ..models.sync_log_model import SheetSyncLog, TabSummary, RejectedRow

logger = logging.getLogger("teramina")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

TAB_SETUP = "SETUP"
TAB_DAILY_LOG = "DAILY_LOG"
TAB_ABW_SAMPLING = "ABW_SAMPLING"
TAB_MORTALITY = "MORTALITY"
TAB_COST = "COST"
TAB_HARVEST = "HARVEST"
TAB_SYNC_LOG = "SYNC_LOG"
SYNC_LOCK_KEY_PREFIX = "sheet_sync_lock:"

SYNC_TAB_RANGES = {
    TAB_DAILY_LOG: f"{TAB_DAILY_LOG}!A3:X",
    TAB_ABW_SAMPLING: f"{TAB_ABW_SAMPLING}!A3:N",
    TAB_COST: f"{TAB_COST}!A3:M",
    TAB_HARVEST: f"{TAB_HARVEST}!A3:N",
    TAB_MORTALITY: f"{TAB_MORTALITY}!A3:H",
}

FEEDBACK_COLUMNS = {
    TAB_DAILY_LOG: ("W", "X"),
    TAB_ABW_SAMPLING: ("M", "N"),
    TAB_MORTALITY: ("G", "H"),
    TAB_COST: ("L", "M"),
    TAB_HARVEST: ("M", "N"),
}
ROW_ID_COLUMNS = {
    TAB_DAILY_LOG: ("U", 20),
    TAB_ABW_SAMPLING: ("K", 10),
    TAB_MORTALITY: ("E", 4),
    TAB_COST: ("J", 9),
    TAB_HARVEST: ("K", 10),
}
TRANSIENT_GOOGLE_STATUSES = {429, 500, 502, 503, 504}
ERROR_CATEGORY_GOOGLE_AUTH = "google_auth"
ERROR_CATEGORY_GOOGLE_QUOTA = "google_quota"
ERROR_CATEGORY_GOOGLE_TRANSIENT = "google_transient"
ERROR_CATEGORY_VALIDATION = "validation"
ERROR_CATEGORY_DATABASE_WRITE = "database_write"
ERROR_CATEGORY_LOCK_CONTENTION = "lock_contention"
ERROR_CATEGORY_STALE_PREVIEW = "stale_preview"
ERROR_CATEGORY_UNKNOWN = "unknown"

# DAILY_LOG column layout (0-indexed):
# A=0  date          B=1  doc           C=2  do_morning     D=3  do_afternoon
# E=4  do_avg        F=5  temp_morning  G=6  temp_afternoon H=7  temp_avg
# I=8  ph_morning    J=9  ph_afternoon  K=10 salinity       L=11 nh3
# M=12 turbidity     N=13 feed_given_kg O=14 feed_leftover  P=15 feed_type
# Q=16 protein_pct   R=17 feeding_freq  S=18 notes
# T=19 status/formula U=20 row_id V=21 delete_marker


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_sheets_service():
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set")
    creds = service_account.Credentials.from_service_account_file(cred_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def _get_drive_service():
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set")
    creds = service_account.Credentials.from_service_account_file(cred_path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _get_sheet_values(service, spreadsheet_id: str, range_name: str) -> list:
    last_exc = None
    for attempt in range(3):
        try:
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            return result.get("values", [])
        except HttpError as exc:
            last_exc = exc
            status = getattr(getattr(exc, "resp", None), "status", None)
            if status not in TRANSIENT_GOOGLE_STATUSES or attempt == 2:
                logger.error("Sheets read error for %s/%s: %s", spreadsheet_id, range_name, exc)
                raise
            time.sleep(0.2 * (attempt + 1))
    raise last_exc


def _check_spreadsheet_access(spreadsheet_id: str) -> tuple[str, str | None]:
    try:
        service = _get_sheets_service()
        _get_sheet_values(service, spreadsheet_id, f"{TAB_SETUP}!A1:B2")
        return "ok", None
    except Exception as exc:
        return "error", str(exc)


def _fingerprint_sheet_rows(rows_by_tab: dict) -> str:
    payload = json.dumps(rows_by_tab, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _append_sync_log(service, spreadsheet_id: str, tab: str, rows_processed: int,
                     rows_inserted: int, rows_updated: int, rows_skipped: int,
                     rows_rejected: int, status: str, error: str = "") -> None:
    try:
        row = [[
            datetime.utcnow().isoformat(),
            tab,
            rows_processed,
            rows_inserted,
            rows_updated,
            rows_skipped,
            rows_rejected,
            status,
            error,
        ]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{TAB_SYNC_LOG}!A:I",
            valueInputOption="RAW",
            body={"values": row},
        ).execute()
    except Exception as exc:
        logger.warning("Failed to write SYNC_LOG: %s", exc)


def _write_sheet_feedback(service, spreadsheet_id: str, rejected_rows: list) -> None:
    if not rejected_rows:
        return

    data = []
    for row in rejected_rows:
        row_number = row.get("row_number")
        tab = row.get("tab")
        if not row_number or tab not in FEEDBACK_COLUMNS:
            continue
        status_col, message_col = FEEDBACK_COLUMNS[tab]
        severity = "WARN" if row.get("reason", "").startswith("warn:") else "ERROR"
        message = f"{row.get('field') or ''}: {row.get('reason') or ''}".strip(": ")
        data.append({
            "range": f"{tab}!{status_col}{row_number}:{message_col}{row_number}",
            "values": [[severity, message]],
        })

    if not data:
        return

    try:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "RAW", "data": data},
        ).execute()
    except Exception as exc:
        logger.warning("Failed to write sheet feedback: %s", exc)


def _backfill_row_ids(service, spreadsheet_id: str) -> int:
    data = []
    for tab, range_name in SYNC_TAB_RANGES.items():
        row_id_col, row_id_idx = ROW_ID_COLUMNS[tab]
        try:
            rows = _get_sheet_values(service, spreadsheet_id, range_name)
        except Exception as exc:
            logger.warning("Failed to inspect row IDs for %s: %s", tab, exc)
            continue

        for row_idx, row in enumerate(rows):
            if not row or not _col(row, 0):
                continue
            if _safe_str(_col(row, row_id_idx)):
                continue
            sheet_row = row_idx + 3
            data.append({
                "range": f"{tab}!{row_id_col}{sheet_row}",
                "values": [[f"{tab}-{sheet_row}"]],
            })

    if not data:
        return 0

    try:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "RAW", "data": data},
        ).execute()
        return len(data)
    except Exception as exc:
        logger.warning("Failed to backfill sheet row IDs: %s", exc)
        return 0


def _safe_float(val, default=None):
    try:
        return float(val) if val not in (None, "", "N/A", "-") else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=None):
    try:
        return int(float(val)) if val not in (None, "", "N/A", "-") else default
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=""):
    return str(val).strip() if val not in (None, "") else default


def _normalize_date(val) -> str | None:
    """
    Normalize any common date string to YYYY-MM-DD.
    Handles: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, DD-Mon-YY/YYYY, DD Month YYYY.
    Returns None if value is empty or unparseable.
    """
    if not val:
        return None
    s = str(val).strip()
    if not s or s in ("N/A", "-", ""):
        return None

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%d-%b-%y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Last resort: return as-is if it already looks like YYYY-MM-DD
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    logger.warning("Could not normalize date: %r", s)
    return None  # unparseable — reject the row


def _auto_fill_doc(date_str: str, start_date) -> int | None:
    """Compute DOC as (date - start_date).days. Returns None if inputs invalid."""
    if not date_str or not start_date:
        return None
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        if isinstance(start_date, datetime):
            s = start_date.date()
        elif isinstance(start_date, date_type):
            s = start_date
        else:
            return None
        return max(1, (d - s).days + 1)
    except (ValueError, TypeError):
        return None


def _col(row: list, idx: int, default=None):
    """Safe column access."""
    return row[idx] if len(row) > idx else default


def _row_identity(row: list, row_idx: int, fallback_key: str) -> str:
    raw = _safe_str(_col(row, row_idx))
    return raw or fallback_key


def _is_delete_marker(val) -> bool:
    return _safe_str(val).upper() in ("Y", "YES", "TRUE", "1", "DELETE", "DELETED")


def _safe_uuid_str(value) -> str | None:
    return str(value) if value else None


def _error_category(error: str = "", exc: Exception | None = None) -> str:
    status = getattr(getattr(exc, "resp", None), "status", None)
    if status in (401, 403):
        return ERROR_CATEGORY_GOOGLE_AUTH
    if status == 429:
        return ERROR_CATEGORY_GOOGLE_QUOTA
    if status in TRANSIENT_GOOGLE_STATUSES:
        return ERROR_CATEGORY_GOOGLE_TRANSIENT

    text = f"{error or ''} {str(exc) if exc else ''}".lower()
    if "sheet changed since preview" in text:
        return ERROR_CATEGORY_STALE_PREVIEW
    if "sync already in progress" in text:
        return ERROR_CATEGORY_LOCK_CONTENTION
    if "quota" in text:
        return ERROR_CATEGORY_GOOGLE_QUOTA
    if "permission" in text or "forbidden" in text or "unauthorized" in text or "cannot access" in text:
        return ERROR_CATEGORY_GOOGLE_AUTH
    if "hard_failure" in text or "invalid" in text or "strict import blocked" in text or "validation" in text:
        return ERROR_CATEGORY_VALIDATION
    if "database" in text or "mongo" in text or "save" in text:
        return ERROR_CATEGORY_DATABASE_WRITE
    if "google" in text or "sheets" in text:
        return ERROR_CATEGORY_GOOGLE_TRANSIENT
    return ERROR_CATEGORY_UNKNOWN


def _sync_error_category(summary: dict, rejected_rows: list) -> str | None:
    for tab_data in summary.values():
        if "error" in tab_data:
            return _error_category(tab_data.get("error") or "")
    if rejected_rows:
        return ERROR_CATEGORY_VALIDATION
    return None


def _persist_failed_sync_log(
    cycle_id: str,
    spreadsheet_id: str,
    sync_uuid,
    started_at: datetime,
    message: str,
    error_category: str,
    source_fingerprint: str = None,
):
    try:
        finished_at = datetime.utcnow()
        sync_log_kwargs = {
            "cycle_id": cycle_id,
            "spreadsheet_id": spreadsheet_id,
            "source_fingerprint": source_fingerprint,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": (finished_at - started_at).total_seconds(),
            "rows_per_second": 0,
            "status": "error",
            "error_category": error_category,
            "tab_summaries": [
                TabSummary(
                    tab="SYNC",
                    processed=0,
                    error=message,
                    error_category=error_category,
                )
            ],
            "rejected_rows": [],
        }
        if sync_uuid:
            sync_log_kwargs["sync_id"] = sync_uuid
        return SheetSyncLog(**sync_log_kwargs).save().sync_id
    except Exception as exc:
        logger.warning("Failed to save failed SheetSyncLog: %s", exc)
        return None


def _delete_result_rows(cycle_data: CycleData | None, cycle_id: str, keys: set[str]) -> int:
    if not keys:
        return 0
    if cycle_data is None:
        cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    if not cycle_data or not cycle_data.result_data:
        return 0

    before = len(cycle_data.result_data)
    cycle_data.result_data = [
        r for r in cycle_data.result_data
        if (r.get("sheet_row_id") or str(r.get("date", ""))) not in keys
    ]
    deleted = before - len(cycle_data.result_data)
    if deleted:
        cycle_data.last_updated = datetime.utcnow()
        cycle_data.save()
    return deleted


def _share_spreadsheet(spreadsheet_id: str, email: str) -> None:
    """Share a spreadsheet with the given email as Editor via Drive API."""
    try:
        drive = _get_drive_service()
        drive.permissions().create(
            fileId=spreadsheet_id,
            body={"type": "user", "role": "writer", "emailAddress": email},
            sendNotificationEmail=False,
        ).execute()
    except Exception as exc:
        logger.warning("Failed to share spreadsheet %s with %s: %s", spreadsheet_id, email, exc)


def _upsert_result_data(cycle_data: CycleData | None, cycle_id: str, new_rows: list) -> CycleData:
    """
    Upsert rows into CycleData.result_data by date key.
    - If date exists: merge non-null new fields (never overwrite existing with None).
    - If date is new: append.
    Returns the saved CycleData document.
    """
    if cycle_data is None:
        cycle_data = CycleData.objects(cycle_id=cycle_id).first()

    if cycle_data and cycle_data.result_data:
        date_map = {str(r.get("date", "")): i for i, r in enumerate(cycle_data.result_data)}
        for row in new_rows:
            key = str(row.get("date", ""))
            if key in date_map:
                existing = cycle_data.result_data[date_map[key]]
                for field, value in row.items():
                    if value is not None and value != "":
                        existing[field] = value
            else:
                cycle_data.result_data.append(row)
                date_map[key] = len(cycle_data.result_data) - 1
        cycle_data.last_updated = datetime.utcnow()
        cycle_data.save()
    else:
        if cycle_data:
            cycle_data.result_data = new_rows
            cycle_data.last_updated = datetime.utcnow()
            cycle_data.save()
        else:
            cycle_data = CycleData(
                cycle_id=cycle_id,
                result_data=new_rows,
                last_updated=datetime.utcnow(),
            ).save()
    return cycle_data


def _validate_entries(
    entries: list,
    col_rename: dict,
    tab: str,
    date_to_sheet_row: dict,
    collector: list,
) -> tuple:
    """
    Run physiological validate_cycle_data on a list of parsed row entries.
    Returns (hard_failed_dates: set, filtered_entries: list).
    Hard-failed rows are removed from filtered_entries and appended to collector.
    Warning rows remain in filtered_entries but are also appended to collector.
    """
    if not entries:
        return set(), entries

    df = pd.DataFrame(entries)
    val_df = df.rename(columns=col_rename)
    report = validate_cycle_data(val_df)

    if not report.hard_failures and not report.warnings:
        return set(), entries

    reverse_rename = {v: k for k, v in col_rename.items()}

    # Map doc → date for issue lookup
    doc_to_date = {e.get("doc"): e["date"] for e in entries if e.get("doc") is not None}

    hard_failed_dates: set = set()
    for issue in report.hard_failures:
        date_str = doc_to_date.get(issue.doc)
        if date_str:
            hard_failed_dates.add(date_str)
            original_field = reverse_rename.get(issue.col, issue.col)
            collector.append({
                "tab": tab,
                "row_number": date_to_sheet_row.get(date_str, 0),
                "field": original_field,
                "raw_value": str(issue.value),
                "reason": f"hard_failure:{issue.col}",
            })

    for issue in report.warnings:
        date_str = doc_to_date.get(issue.doc)
        if date_str and date_str not in hard_failed_dates:
            original_field = reverse_rename.get(issue.col, issue.col)
            collector.append({
                "tab": tab,
                "row_number": date_to_sheet_row.get(date_str, 0),
                "field": original_field,
                "raw_value": str(issue.value),
                "reason": f"warn:{issue.reason}",
            })

    filtered = [e for e in entries if e["date"] not in hard_failed_dates]
    return hard_failed_dates, filtered


# ── Service ───────────────────────────────────────────────────────────────────

class SheetService:

    @staticmethod
    def connect(user_id: str, cycle_id: str, spreadsheet_id: str):
        """Link a Google Sheet to a cycle. Validates access first."""
        try:
            service = _get_sheets_service()
            # Validate access by reading the SETUP tab directly (bypass _get_sheet_values
            # which silently swallows HttpError and returns []).
            try:
                service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=f"{TAB_SETUP}!A1:B2",
                ).execute()
            except HttpError:
                return 400, DataErrorSchema(
                    code=400,
                    message="Cannot access spreadsheet. Make sure it is shared with the service account."
                )
            existing = SheetIntegration.objects(cycle_id=cycle_id).first()
            if existing:
                existing.spreadsheet_id = spreadsheet_id
                existing.spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                existing.is_active = True
                existing.last_status = "pending"
                existing.save()
            else:
                SheetIntegration(
                    cycle_id=cycle_id,
                    user_id=user_id,
                    spreadsheet_id=spreadsheet_id,
                    spreadsheet_url=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
                ).save()
            return 200, DataSuccessSchema(
                code=200,
                message="Sheet connected successfully",
                payload={"cycle_id": cycle_id, "spreadsheet_id": spreadsheet_id},
            )
        except Exception as exc:
            logger.exception("Sheet connect error: %s", exc)
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def disconnect(cycle_id: str):
        integration = SheetIntegration.objects(cycle_id=cycle_id).first()
        if not integration:
            return 400, DataErrorSchema(code=400, message="No sheet integration found for this cycle")
        integration.is_active = False
        integration.save()
        return 200, DataSuccessSchema(code=200, message="Sheet disconnected", payload={})

    @staticmethod
    def get_status(cycle_id: str):
        """Always 200 — is_active:false when no integration."""
        integration = SheetIntegration.objects(cycle_id=cycle_id).first()
        if not integration:
            return 200, DataSuccessSchema(
                code=200,
                message="OK",
                payload={"cycle_id": cycle_id, "is_active": False},
            )

        # Embed latest sync log tab_summaries if available
        tab_summaries = []
        rows_per_second = None
        error_category = getattr(integration, "last_error_category", None)
        if integration.last_sync_log_id:
            log = SheetSyncLog.objects(sync_id=integration.last_sync_log_id).first()
            if log:
                rows_per_second = getattr(log, "rows_per_second", None)
                error_category = getattr(log, "error_category", None) or error_category
                tab_summaries = [
                    {
                        "tab": ts.tab,
                        "processed": ts.processed,
                        "inserted": ts.inserted,
                        "updated": ts.updated,
                        "deleted": getattr(ts, "deleted", 0),
                        "skipped": ts.skipped,
                        "rejected": ts.rejected,
                        "error": ts.error,
                        "error_category": getattr(ts, "error_category", None),
                    }
                    for ts in log.tab_summaries
                ]

        access_status = "not_checked"
        access_error = None
        if integration.is_active and os.getenv("SHEETS_STATUS_ACCESS_CHECK", "").lower() == "true":
            access_status, access_error = _check_spreadsheet_access(integration.spreadsheet_id)

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "cycle_id": cycle_id,
                "spreadsheet_id": integration.spreadsheet_id,
                "spreadsheet_url": integration.spreadsheet_url,
                "is_active": integration.is_active,
                "last_synced": integration.last_synced.isoformat() if integration.last_synced else None,
                "last_status": integration.last_status,
                "last_error": integration.last_error,
                "rows_synced": integration.rows_synced,
                "active_sync_id": _safe_uuid_str(getattr(integration, "active_sync_id", None)),
                "last_sync_id": _safe_uuid_str(getattr(integration, "last_sync_log_id", None)),
                "access_status": access_status,
                "access_error": access_error,
                "rows_per_second": rows_per_second,
                "error_category": error_category or (_error_category(integration.last_error or "") if integration.last_error else None),
                "tab_summaries": tab_summaries,
            },
        )

    @staticmethod
    def sync_cycle(
        cycle_id: str,
        dry_run: bool = False,
        expected_fingerprint: str = None,
        sync_id: str | UUID = None,
    ) -> dict:
        """
        Pull data from all tabs and upsert into MongoDB.
        If dry_run=True, validate and parse everything but write nothing to DB.
        Returns dict with per-tab summary, rejected_rows list, and overall status.
        """
        integration = SheetIntegration.objects(cycle_id=cycle_id, is_active=True).first()
        if not integration:
            return {"error": "No active integration found"}

        started_at = datetime.utcnow()
        sync_uuid = UUID(str(sync_id)) if sync_id else None
        cycle = Cycle.objects(id=cycle_id).first()
        if not cycle:
            if not dry_run:
                integration.last_status = "error"
                integration.last_error = "Cycle not found"
                integration.last_error_category = ERROR_CATEGORY_UNKNOWN
                integration.active_sync_id = None
                integration.save()
            return {"error": "Cycle not found", "error_category": ERROR_CATEGORY_UNKNOWN}

        spreadsheet_id = integration.spreadsheet_id
        start_date = cycle.start_date
        summary = {}
        total_inserted = 0
        total_updated = 0
        rejected_rows_collector: list = []

        try:
            service = _get_sheets_service()
        except Exception as exc:
            category = _error_category(exc=exc)
            if not dry_run:
                integration.last_status = "error"
                integration.last_error = str(exc)
                integration.last_error_category = category
                integration.active_sync_id = None
                log_id = _persist_failed_sync_log(
                    cycle_id,
                    spreadsheet_id,
                    sync_uuid,
                    started_at,
                    str(exc),
                    category,
                )
                if log_id:
                    integration.last_sync_log_id = log_id
                integration.save()
            return {"error": str(exc), "error_category": category}

        row_ids_backfilled = _backfill_row_ids(service, spreadsheet_id)

        rows_by_tab = {}
        read_errors = {}
        for tab, range_name in SYNC_TAB_RANGES.items():
            try:
                rows_by_tab[tab] = _get_sheet_values(service, spreadsheet_id, range_name)
            except HttpError as exc:
                rows_by_tab[tab] = []
                read_errors[tab] = str(exc)

        source_fingerprint = _fingerprint_sheet_rows(rows_by_tab)
        if expected_fingerprint and expected_fingerprint != source_fingerprint:
            message = "Sheet changed since preview. Run preview-sync again."
            category = ERROR_CATEGORY_STALE_PREVIEW
            if not dry_run:
                integration.last_status = "error"
                integration.last_error = message
                integration.last_error_category = category
                integration.active_sync_id = None
                log_id = _persist_failed_sync_log(
                    cycle_id,
                    spreadsheet_id,
                    sync_uuid,
                    started_at,
                    message,
                    category,
                    source_fingerprint=source_fingerprint,
                )
                if log_id:
                    integration.last_sync_log_id = log_id
                integration.save()
            return {"error": message, "error_category": category}

        if not dry_run:
            integration.last_status = "syncing"
            integration.active_sync_id = sync_uuid
            integration.save()

        # ── DAILY_LOG ─────────────────────────────────────────────────────────
        try:
            if TAB_DAILY_LOG in read_errors:
                raise RuntimeError(read_errors[TAB_DAILY_LOG])
            rows = rows_by_tab[TAB_DAILY_LOG]
            inserted = updated = deleted = skipped = rejected = 0

            cycle_data = CycleData.objects(cycle_id=cycle_id).first()
            existing_dates = {}
            if cycle_data and cycle_data.result_data:
                existing_dates = {
                    str(r.get("date", "")): i
                    for i, r in enumerate(cycle_data.result_data)
                }

            new_or_updated = []
            delete_keys = set()
            date_to_sheet_row: dict = {}

            for row_idx, row in enumerate(rows):
                sheet_row = row_idx + 3  # rows 1–2 are headers
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                row_key = _row_identity(row, 20, date_str or f"{TAB_DAILY_LOG}:{sheet_row}")
                if _is_delete_marker(_col(row, 21)):
                    delete_keys.add(row_key)
                    continue
                if not date_str:
                    rejected += 1
                    rejected_rows_collector.append({
                        "tab": TAB_DAILY_LOG, "row_number": sheet_row,
                        "field": "date", "raw_value": str(_col(row, 0) or ""),
                        "reason": "invalid_date",
                    })
                    continue

                doc = _safe_int(_col(row, 1)) or _auto_fill_doc(date_str, start_date)
                do_morning = _safe_float(_col(row, 2))
                do_afternoon = _safe_float(_col(row, 3))
                do_avg = _safe_float(_col(row, 4)) or (
                    round((do_morning + do_afternoon) / 2, 2)
                    if do_morning is not None and do_afternoon is not None else None
                )
                temp_morning = _safe_float(_col(row, 5))
                temp_afternoon = _safe_float(_col(row, 6))
                temp_avg = _safe_float(_col(row, 7)) or (
                    round((temp_morning + temp_afternoon) / 2, 2)
                    if temp_morning is not None and temp_afternoon is not None else None
                )

                entry = {
                    "date": date_str, "doc": doc,
                    "sheet_row_id": row_key,
                    "do_morning": do_morning, "do_afternoon": do_afternoon, "do_avg": do_avg,
                    "temp_morning": temp_morning, "temp_afternoon": temp_afternoon,
                    "temp_avg": temp_avg,
                    "ph_morning": _safe_float(_col(row, 8)),
                    "ph_afternoon": _safe_float(_col(row, 9)),
                    "salinity": _safe_float(_col(row, 10)),
                    "nh3": _safe_float(_col(row, 11)),
                    "turbidity": _safe_float(_col(row, 12)),
                    "feed_given_kg": _safe_float(_col(row, 13)),
                    "feed_leftover": _safe_float(_col(row, 14)),
                    "feed_type": _safe_str(_col(row, 15)),
                    "protein_content": _safe_float(_col(row, 16)),
                    "feeding_frequency": _safe_int(_col(row, 17)),
                    "notes": _safe_str(_col(row, 18)),
                    "source": "google_sheets",
                }
                date_to_sheet_row[date_str] = sheet_row
                if date_str in existing_dates:
                    updated += 1
                else:
                    inserted += 1
                new_or_updated.append(entry)

            # Physiological validation (DO, temperature, NH3 bounds)
            if new_or_updated:
                hard_failed, new_or_updated = _validate_entries(
                    entries=new_or_updated,
                    col_rename={"do_avg": "do", "temp_avg": "temperature"},
                    tab=TAB_DAILY_LOG,
                    date_to_sheet_row=date_to_sheet_row,
                    collector=rejected_rows_collector,
                )
                if hard_failed:
                    rejected += len(hard_failed)
                    inserted = sum(1 for e in new_or_updated if e["date"] not in existing_dates)
                    updated = sum(1 for e in new_or_updated if e["date"] in existing_dates)

            if new_or_updated and not dry_run:
                cycle_data = _upsert_result_data(cycle_data, cycle_id, new_or_updated)

                # Cascade: upsert FeedRealization for rows with feed data
                feed_entries = [e for e in new_or_updated if e.get("feed_given_kg") and e.get("doc")]
                if feed_entries:
                    existing_feed_docs = {
                        r.doc for r in FeedRealization.objects(cycle_id=cycle_id).only("doc")
                    }
                    for fe in feed_entries:
                        doc_val = fe["doc"]
                        if doc_val in existing_feed_docs:
                            update_fields = {
                                "set__feed_given": fe["feed_given_kg"],
                                "set__feed_ration": fe["feed_given_kg"],
                                "set__last_updated": datetime.utcnow(),
                            }
                            if fe.get("feed_leftover") is not None:
                                update_fields["set__feed_leftover"] = fe["feed_leftover"]
                            FeedRealization.objects(
                                cycle_id=cycle_id, doc=doc_val
                            ).update_one(**update_fields)
                        else:
                            FeedRealization(
                                cycle_id=cycle_id,
                                doc=doc_val,
                                ration_number=0,
                                feed_ration=fe["feed_given_kg"],
                                feed_given=fe["feed_given_kg"],
                                feed_leftover=fe.get("feed_leftover"),
                                last_updated=datetime.utcnow(),
                            ).save()
                            existing_feed_docs.add(doc_val)
            if delete_keys and not dry_run:
                deleted = _delete_result_rows(cycle_data, cycle_id, delete_keys)

            total_inserted += inserted
            total_updated += updated
            summary[TAB_DAILY_LOG] = {
                "inserted": inserted, "updated": updated, "deleted": deleted,
                "skipped": skipped, "rejected": rejected,
            }
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_DAILY_LOG,
                                 inserted + updated + deleted + skipped + rejected,
                                 inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("DAILY_LOG sync error: %s", exc)
            summary[TAB_DAILY_LOG] = {"error": str(exc)}
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_DAILY_LOG,
                                 0, 0, 0, 0, 0, "error", str(exc))

        # ── ABW_SAMPLING ──────────────────────────────────────────────────────
        try:
            if TAB_ABW_SAMPLING in read_errors:
                raise RuntimeError(read_errors[TAB_ABW_SAMPLING])
            rows = rows_by_tab[TAB_ABW_SAMPLING]
            inserted = updated = deleted = skipped = rejected = 0

            cycle_data = CycleData.objects(cycle_id=cycle_id).first()
            existing_abw_dates = set()
            if cycle_data and cycle_data.result_data:
                existing_abw_dates = {
                    str(r.get("date", ""))
                    for r in cycle_data.result_data
                    if r.get("abw") is not None
                }

            new_abw = []
            delete_keys = set()
            abw_date_to_sheet_row: dict = {}

            for row_idx, row in enumerate(rows):
                sheet_row = row_idx + 3
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                row_key = _row_identity(row, 10, date_str or f"{TAB_ABW_SAMPLING}:{sheet_row}")
                if _is_delete_marker(_col(row, 11)):
                    delete_keys.add(row_key)
                    continue
                if not date_str:
                    rejected += 1
                    rejected_rows_collector.append({
                        "tab": TAB_ABW_SAMPLING, "row_number": sheet_row,
                        "field": "date", "raw_value": str(_col(row, 0) or ""),
                        "reason": "invalid_date",
                    })
                    continue
                abw_val = _safe_float(_col(row, 4))
                if abw_val is None:
                    raw_abw = _col(row, 4)
                    if raw_abw not in (None, "", "N/A", "-"):
                        rejected_rows_collector.append({
                            "tab": TAB_ABW_SAMPLING, "row_number": sheet_row,
                            "field": "abw", "raw_value": str(raw_abw),
                            "reason": "invalid_number:abw",
                        })
                    rejected += 1
                    continue

                doc = _safe_int(_col(row, 1)) or _auto_fill_doc(date_str, start_date)
                entry = {
                    "date": date_str, "doc": doc,
                    "sheet_row_id": row_key,
                    "abw_sample_count": _safe_int(_col(row, 2)),
                    "abw_total_weight_g": _safe_float(_col(row, 3)),
                    "abw": abw_val,
                    "abw_min_g": _safe_float(_col(row, 5)),
                    "abw_max_g": _safe_float(_col(row, 6)),
                    "abw_cv_pct": _safe_float(_col(row, 7)),
                    "sampled_by": _safe_str(_col(row, 8)),
                    "abw_notes": _safe_str(_col(row, 9)),
                    "source": "google_sheets",
                }
                abw_date_to_sheet_row[date_str] = sheet_row
                if date_str in existing_abw_dates:
                    updated += 1
                else:
                    inserted += 1
                new_abw.append(entry)

            # Physiological validation on ABW values
            if new_abw:
                hard_failed, new_abw = _validate_entries(
                    entries=new_abw,
                    col_rename={},
                    tab=TAB_ABW_SAMPLING,
                    date_to_sheet_row=abw_date_to_sheet_row,
                    collector=rejected_rows_collector,
                )
                if hard_failed:
                    rejected += len(hard_failed)
                    inserted = sum(1 for e in new_abw if e["date"] not in existing_abw_dates)
                    updated = sum(1 for e in new_abw if e["date"] in existing_abw_dates)

            if new_abw and not dry_run:
                _upsert_result_data(cycle_data, cycle_id, new_abw)
            if delete_keys and not dry_run:
                deleted = _delete_result_rows(cycle_data, cycle_id, delete_keys)

            total_inserted += inserted
            total_updated += updated
            summary[TAB_ABW_SAMPLING] = {
                "inserted": inserted, "updated": updated, "deleted": deleted,
                "skipped": skipped, "rejected": rejected,
            }
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_ABW_SAMPLING,
                                 inserted + updated + deleted + skipped + rejected,
                                 inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("ABW_SAMPLING sync error: %s", exc)
            summary[TAB_ABW_SAMPLING] = {"error": str(exc)}
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_ABW_SAMPLING,
                                 0, 0, 0, 0, 0, "error", str(exc))

        # ── COST ──────────────────────────────────────────────────────────────
        # Cost is stored per cycle_id in CostData.farm_id — costs are cycle-scoped.
        try:
            if TAB_COST in read_errors:
                raise RuntimeError(read_errors[TAB_COST])
            rows = rows_by_tab[TAB_COST]
            inserted = updated = deleted = skipped = rejected = 0

            cost_doc = CostData.objects(farm_id=cycle_id).first()
            existing_key_to_index = {}
            if cost_doc and cost_doc.data:
                existing_key_to_index = {
                    r.get("sheet_row_id") or f"{r.get('date')}_{r.get('category')}_{r.get('description')}": i
                    for i, r in enumerate(cost_doc.data)
                }

            new_costs = []
            delete_keys = set()
            for row_idx, row in enumerate(rows):
                sheet_row = row_idx + 3
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                category = _safe_str(_col(row, 1))
                description = _safe_str(_col(row, 2))
                key = _row_identity(row, 9, f"{date_str}_{category}_{description}")
                if _is_delete_marker(_col(row, 10)):
                    delete_keys.add(key)
                    continue
                if not date_str:
                    rejected += 1
                    rejected_rows_collector.append({
                        "tab": TAB_COST, "row_number": sheet_row,
                        "field": "date", "raw_value": str(_col(row, 0) or ""),
                        "reason": "invalid_date",
                    })
                    continue
                # Flag non-parseable unit_price if the cell was non-empty
                raw_price = _col(row, 5)
                unit_price = _safe_float(raw_price)
                if unit_price is None and raw_price not in (None, "", "N/A", "-"):
                    rejected_rows_collector.append({
                        "tab": TAB_COST, "row_number": sheet_row,
                        "field": "unit_price", "raw_value": str(raw_price),
                        "reason": "warn:invalid_number:unit_price",
                    })

                entry = {
                    "date": date_str, "sheet_row_id": key,
                    "category": category, "description": description,
                    "quantity": _safe_float(_col(row, 3)),
                    "unit": _safe_str(_col(row, 4)),
                    "unit_price": unit_price,
                    "total": _safe_float(_col(row, 6)),
                    "vendor": _safe_str(_col(row, 7)),
                    "notes": _safe_str(_col(row, 8)),
                    "source": "google_sheets",
                }
                if key in existing_key_to_index:
                    existing_index = existing_key_to_index[key]
                    if existing_index is None:
                        skipped += 1
                        continue
                    if cost_doc and not dry_run:
                        existing_cost = cost_doc.data[existing_index]
                        for field, value in entry.items():
                            if value is not None and value != "":
                                existing_cost[field] = value
                    updated += 1
                else:
                    new_costs.append(entry)
                    existing_key_to_index[key] = None
                    inserted += 1

            if delete_keys:
                existing_delete_count = sum(1 for key in delete_keys if key in existing_key_to_index)
                deleted += existing_delete_count
                skipped += len(delete_keys) - existing_delete_count
                if cost_doc and not dry_run and existing_delete_count:
                    cost_doc.data = [
                        row for row in cost_doc.data
                        if (row.get("sheet_row_id") or f"{row.get('date')}_{row.get('category')}_{row.get('description')}") not in delete_keys
                    ]

            if (new_costs or updated or deleted) and not dry_run:
                if cost_doc:
                    cost_doc.data.extend(new_costs)
                    cost_doc.last_updated = datetime.utcnow()
                    cost_doc.save()
                else:
                    CostData(
                        farm_id=cycle_id,
                        data=new_costs,
                        last_updated=datetime.utcnow(),
                    ).save()

            total_inserted += inserted
            total_updated += updated
            summary[TAB_COST] = {
                "inserted": inserted, "updated": updated, "deleted": deleted,
                "skipped": skipped, "rejected": rejected,
            }
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_COST,
                                 inserted + updated + deleted + skipped + rejected,
                                 inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("COST sync error: %s", exc)
            summary[TAB_COST] = {"error": str(exc)}
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_COST,
                                 0, 0, 0, 0, 0, "error", str(exc))

        # ── HARVEST ───────────────────────────────────────────────────────────
        try:
            if TAB_HARVEST in read_errors:
                raise RuntimeError(read_errors[TAB_HARVEST])
            rows = rows_by_tab[TAB_HARVEST]
            inserted = updated = deleted = skipped = rejected = 0

            existing_harvest = HarvestRecord.objects(cycle_id=cycle_id)
            existing_harvest_keys = {
                r.harvest_data.get("sheet_row_id") or str(r.harvest_data.get("date", ""))
                for r in existing_harvest
            }

            new_harvest = []
            for row_idx, row in enumerate(rows):
                sheet_row = row_idx + 3
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                row_key = _row_identity(row, 10, date_str or f"{TAB_HARVEST}:{sheet_row}")
                if _is_delete_marker(_col(row, 11)):
                    lookup = {"harvest_data__date": date_str} if not _safe_str(_col(row, 10)) else {"harvest_data__sheet_row_id": row_key}
                    if not dry_run:
                        deleted += HarvestRecord.objects(cycle_id=cycle_id, **lookup).delete()
                    else:
                        deleted += 1
                    continue
                if not date_str:
                    rejected += 1
                    rejected_rows_collector.append({
                        "tab": TAB_HARVEST, "row_number": sheet_row,
                        "field": "date", "raw_value": str(_col(row, 0) or ""),
                        "reason": "invalid_date",
                    })
                    continue
                biomass = _safe_float(_col(row, 3))
                if biomass is None:
                    raw_biomass = _col(row, 3)
                    if raw_biomass not in (None, "", "N/A", "-"):
                        rejected_rows_collector.append({
                            "tab": TAB_HARVEST, "row_number": sheet_row,
                            "field": "harvest_biomass_kg", "raw_value": str(raw_biomass),
                            "reason": "missing_required:harvest_biomass_kg",
                        })
                    rejected += 1
                    continue

                doc = _safe_int(_col(row, 1)) or _auto_fill_doc(date_str, start_date)
                is_partial_raw = _safe_str(_col(row, 2)).upper()
                is_partial = is_partial_raw in ("Y", "YES", "1", "TRUE")

                harvest_data = {
                    "date": date_str,
                    "sheet_row_id": row_key,
                    "doc": doc, "is_partial": is_partial,
                    "harvest_biomass_kg": biomass,
                    "abw_g": _safe_float(_col(row, 4)),
                    "sr_pct": _safe_float(_col(row, 5)),
                    "bags": _safe_int(_col(row, 6)),
                    "buyer": _safe_str(_col(row, 7)),
                    "price_per_kg_idr": _safe_float(_col(row, 8)),
                    "notes": _safe_str(_col(row, 9)),
                    "source": "google_sheets",
                }

                harvest_key = harvest_data["sheet_row_id"]
                if harvest_key in existing_harvest_keys:
                    if not dry_run:
                        lookup = {"harvest_data__date": date_str}
                        if _safe_str(_col(row, 10)):
                            lookup = {"harvest_data__sheet_row_id": harvest_key}
                        HarvestRecord.objects(
                            cycle_id=cycle_id,
                            **lookup
                        ).update_one(set__harvest_data=harvest_data, set__last_updated=datetime.utcnow())
                    updated += 1
                else:
                    new_harvest.append(harvest_data)
                    existing_harvest_keys.add(harvest_key)
                    inserted += 1

            if new_harvest and not dry_run:
                for hd in new_harvest:
                    HarvestRecord(
                        cycle_id=cycle_id,
                        harvest_data=hd,
                        last_updated=datetime.utcnow(),
                    ).save()

            total_inserted += inserted
            total_updated += updated
            summary[TAB_HARVEST] = {
                "inserted": inserted, "updated": updated, "deleted": deleted,
                "skipped": skipped, "rejected": rejected,
            }
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_HARVEST,
                                 inserted + updated + deleted + skipped + rejected,
                                 inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("HARVEST sync error: %s", exc)
            summary[TAB_HARVEST] = {"error": str(exc)}
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_HARVEST,
                                 0, 0, 0, 0, 0, "error", str(exc))

        # ── MORTALITY ─────────────────────────────────────────────────────────
        try:
            if TAB_MORTALITY in read_errors:
                raise RuntimeError(read_errors[TAB_MORTALITY])
            rows = rows_by_tab[TAB_MORTALITY]
            inserted = updated = deleted = skipped = rejected = 0
            cycle_data = CycleData.objects(cycle_id=cycle_id).first()
            existing_mortality_keys = set()
            if cycle_data and cycle_data.result_data:
                existing_mortality_keys = {
                    r.get("sheet_row_id") or str(r.get("date", ""))
                    for r in cycle_data.result_data
                    if r.get("mortality_count") is not None
                }

            mortality_rows = []
            delete_keys = set()
            for row_idx, row in enumerate(rows):
                sheet_row = row_idx + 3
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                row_key = _row_identity(row, 4, date_str or f"{TAB_MORTALITY}:{sheet_row}")
                if _is_delete_marker(_col(row, 5)):
                    delete_keys.add(row_key)
                    continue
                if not date_str:
                    rejected += 1
                    rejected_rows_collector.append({
                        "tab": TAB_MORTALITY, "row_number": sheet_row,
                        "field": "date", "raw_value": str(_col(row, 0) or ""),
                        "reason": "invalid_date",
                    })
                    continue
                dead_count = _safe_int(_col(row, 2))
                if dead_count is None:
                    raw_count = _col(row, 2)
                    if raw_count not in (None, "", "N/A", "-"):
                        rejected_rows_collector.append({
                            "tab": TAB_MORTALITY, "row_number": sheet_row,
                            "field": "mortality_count", "raw_value": str(raw_count),
                            "reason": "missing_required:mortality_count",
                        })
                    rejected += 1
                    continue

                doc = _safe_int(_col(row, 1)) or _auto_fill_doc(date_str, start_date)
                entry = {
                    "date": date_str, "doc": doc,
                    "sheet_row_id": row_key,
                    "mortality_count": dead_count,
                    "mortality_notes": _safe_str(_col(row, 3)),
                    "source": "google_sheets",
                }
                mortality_rows.append(entry)
                mortality_key = entry["sheet_row_id"]
                if mortality_key in existing_mortality_keys:
                    updated += 1
                else:
                    inserted += 1
                    existing_mortality_keys.add(mortality_key)

            if mortality_rows and not dry_run:
                _upsert_result_data(cycle_data, cycle_id, mortality_rows)
            if delete_keys and not dry_run:
                deleted = _delete_result_rows(cycle_data, cycle_id, delete_keys)

            total_inserted += inserted
            total_updated += updated
            summary[TAB_MORTALITY] = {
                "inserted": inserted, "updated": updated, "deleted": deleted,
                "skipped": skipped, "rejected": rejected,
            }
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_MORTALITY,
                                 inserted + updated + deleted + skipped + rejected,
                                 inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("MORTALITY sync error: %s", exc)
            summary[TAB_MORTALITY] = {"error": str(exc)}
            if not dry_run:
                _append_sync_log(service, spreadsheet_id, TAB_MORTALITY,
                                 0, 0, 0, 0, 0, "error", str(exc))

        # ── Finalize ──────────────────────────────────────────────────────────
        tab_errors = [v for v in summary.values() if "error" in v]
        successful_tabs = [v for v in summary.values() if "error" not in v]
        has_row_issues = bool(rejected_rows_collector) or any(
            v.get("rejected", 0) > 0 for v in successful_tabs
        )
        if tab_errors and successful_tabs:
            status_str = "partial"
        elif tab_errors:
            status_str = "error"
        elif has_row_issues:
            status_str = "partial"
        else:
            status_str = "ok"
        finished_at = datetime.utcnow()
        duration_seconds = (finished_at - started_at).total_seconds()

        if not dry_run:
            _write_sheet_feedback(service, spreadsheet_id, rejected_rows_collector)
            integration.last_synced = finished_at
            integration.last_status = status_str
            integration.last_error = "; ".join(
                f"{k}: {v['error']}" for k, v in summary.items() if "error" in v
            ) or None
            sync_error_category = _sync_error_category(summary, rejected_rows_collector)
            integration.last_error_category = sync_error_category if status_str != "ok" else None
            integration.rows_synced = (integration.rows_synced or 0) + total_inserted + total_updated

            # Persist sync log
            try:
                tab_summaries = []
                total_processed = 0
                for tab_name, tab_data in summary.items():
                    if "error" not in tab_data:
                        processed = (
                            tab_data.get("inserted", 0) + tab_data.get("updated", 0)
                            + tab_data.get("deleted", 0) + tab_data.get("skipped", 0)
                            + tab_data.get("rejected", 0)
                        )
                        total_processed += processed
                        tab_summaries.append(TabSummary(
                            tab=tab_name,
                            processed=processed,
                            inserted=tab_data.get("inserted", 0),
                            updated=tab_data.get("updated", 0),
                            deleted=tab_data.get("deleted", 0),
                            skipped=tab_data.get("skipped", 0),
                            rejected=tab_data.get("rejected", 0),
                        ))
                    else:
                        tab_summaries.append(TabSummary(
                            tab=tab_name,
                            processed=0,
                            error=tab_data.get("error"),
                            error_category=_error_category(tab_data.get("error") or ""),
                        ))

                rejected_row_docs = [
                    RejectedRow(
                        tab=r["tab"],
                        row_number=r.get("row_number"),
                        field=r.get("field"),
                        raw_value=r.get("raw_value"),
                        reason=r.get("reason"),
                    )
                    for r in rejected_rows_collector
                ]

                sync_log_kwargs = {
                    "cycle_id": cycle_id,
                    "spreadsheet_id": spreadsheet_id,
                    "source_fingerprint": source_fingerprint,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "duration_seconds": duration_seconds,
                    "rows_per_second": round(total_processed / duration_seconds, 2) if duration_seconds > 0 else float(total_processed),
                    "status": status_str,
                    "error_category": sync_error_category,
                    "tab_summaries": tab_summaries,
                    "rejected_rows": rejected_row_docs,
                }
                if sync_uuid:
                    sync_log_kwargs["sync_id"] = sync_uuid

                sync_log = SheetSyncLog(**sync_log_kwargs).save()

                integration.last_sync_log_id = sync_log.sync_id
                integration.active_sync_id = None
            except Exception as log_exc:
                # Log failure must not roll back the sync itself
                logger.warning("Failed to save SheetSyncLog: %s", log_exc)
                integration.active_sync_id = None

            integration.save()

        return {
            "summary": summary,
            "rejected_rows": rejected_rows_collector,
            "source_fingerprint": source_fingerprint,
            "sync_id": str(sync_uuid) if sync_uuid else None,
            "row_ids_backfilled": row_ids_backfilled,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": duration_seconds,
            "rows_per_second": (
                round(
                    sum(
                        data.get("inserted", 0) + data.get("updated", 0) + data.get("deleted", 0)
                        + data.get("skipped", 0) + data.get("rejected", 0)
                        for data in summary.values() if "error" not in data
                    ) / duration_seconds,
                    2,
                )
                if duration_seconds > 0 else 0
            ),
            "status": status_str,
            "error_category": _sync_error_category(summary, rejected_rows_collector),
        }

    @staticmethod
    def create_template(cycle_id: str, user_id: str = None, user_email: str = None) -> tuple:
        """
        Create a new Google Sheet pre-filled with cycle info.
        Shares with user_email, auto-connects the integration, returns URL.
        """
        cycle = Cycle.objects(id=cycle_id).first()
        if not cycle:
            return 400, DataErrorSchema(code=400, message="Cycle not found")
        pond = Pond.objects(id=cycle.pond_id).first()

        try:
            service = _get_sheets_service()

            title = f"Teramina - {getattr(pond, 'name', 'Pond')} - {cycle.name}"
            spreadsheet = service.spreadsheets().create(body={
                "properties": {"title": title},
                "sheets": [
                    {"properties": {"title": TAB_SETUP}},
                    {"properties": {"title": TAB_DAILY_LOG}},
                    {"properties": {"title": TAB_ABW_SAMPLING}},
                    {"properties": {"title": TAB_MORTALITY}},
                    {"properties": {"title": TAB_COST}},
                    {"properties": {"title": TAB_HARVEST}},
                    {"properties": {"title": TAB_SYNC_LOG}},
                ],
            }).execute()

            spreadsheet_id = spreadsheet["spreadsheetId"]
            spreadsheet_url = spreadsheet["spreadsheetUrl"]

            # Map tab title → numeric sheetId for batchUpdate formatting calls
            sheet_id_map = {
                s["properties"]["title"]: s["properties"]["sheetId"]
                for s in spreadsheet.get("sheets", [])
            }

            updates = []

            # SETUP tab
            setup_values = [
                ["Parameter", "Value"],
                ["Farm Name", ""],
                ["Pond Name", getattr(pond, "name", "") if pond else ""],
                ["Cycle Name", cycle.name or ""],
                ["Cycle ID", str(cycle.id)],
                ["Stocking Date", cycle.start_date.strftime("%Y-%m-%d") if cycle.start_date else ""],
                ["Pond Size (m²)", str(getattr(pond, "size", "")) if pond else ""],
                ["Pond Depth (m)", str(getattr(pond, "depth", "")) if pond else ""],
                ["Service Account Email",
                 service_account.Credentials.from_service_account_file(
                     os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), scopes=SCOPES
                 ).service_account_email if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else ""],
                ["Last Synced", ""],
                ["Sync Status", "Not synced yet"],
            ]
            updates.append({
                "range": f"{TAB_SETUP}!A1:B11",
                "values": setup_values,
            })

            # DAILY_LOG — row 1: column names, row 2: units/hints
            updates.append({
                "range": f"{TAB_DAILY_LOG}!A1:X2",
                "values": [
                    ["Date", "DOC", "DO Morning", "DO Afternoon", "DO Average",
                     "Temp Morning", "Temp Afternoon", "Temp Average",
                     "pH Morning", "pH Afternoon", "Salinity", "NH3/Ammonia",
                     "Turbidity", "Feed Given", "Feed Leftover",
                     "Feed Type", "Protein %", "Feeding Freq", "Notes", "Status", "Row ID",
                     "Delete?", "Import Status", "Import Message"],
                    ["YYYY-MM-DD", "days", "mg/L", "mg/L", "mg/L",
                     "°C", "°C", "°C",
                     "", "", "ppt", "mg/L",
                     "Secchi cm", "kg", "kg",
                     "", "%", "times/day", "", "", "Do not edit", "Y to delete", "System", "System"],
                ],
            })

            # ABW_SAMPLING
            updates.append({
                "range": f"{TAB_ABW_SAMPLING}!A1:N2",
                "values": [
                    ["Date", "DOC", "Sample Count", "Total Weight", "ABW",
                     "Min Weight", "Max Weight", "CV%", "Sampled By", "Notes", "Row ID",
                     "Delete?", "Import Status", "Import Message"],
                    ["YYYY-MM-DD", "days", "shrimp", "g", "g (REQUIRED)",
                     "g", "g", "%", "", "", "Do not edit", "Y to delete", "System", "System"],
                ],
            })

            # MORTALITY
            updates.append({
                "range": f"{TAB_MORTALITY}!A1:H2",
                "values": [
                    ["Date", "DOC", "Dead Count", "Notes", "Row ID", "Delete?", "Import Status", "Import Message"],
                    ["YYYY-MM-DD", "days", "shrimp (REQUIRED)", "", "Do not edit", "Y to delete", "System", "System"],
                ],
            })

            # COST
            updates.append({
                "range": f"{TAB_COST}!A1:M2",
                "values": [
                    ["Date", "Category", "Description", "Quantity", "Unit",
                     "Unit Price (IDR)", "Total (IDR)", "Vendor", "Notes", "Row ID",
                     "Delete?", "Import Status", "Import Message"],
                    ["YYYY-MM-DD", "Feed/Chemical/Labor/Electricity/Other",
                     "", "", "kg/L/pcs/day", "", "REQUIRED", "", "", "Do not edit", "Y to delete", "System", "System"],
                ],
            })

            # HARVEST
            updates.append({
                "range": f"{TAB_HARVEST}!A1:N2",
                "values": [
                    ["Date", "DOC", "Is Partial?", "Biomass (kg)", "ABW (g)",
                     "SR (%)", "Bags/Count", "Buyer", "Price/kg (IDR)", "Notes", "Row ID",
                     "Delete?", "Import Status", "Import Message"],
                    ["YYYY-MM-DD", "days", "Y or N", "kg (REQUIRED)", "g",
                     "%", "", "", "", "", "Do not edit", "Y to delete", "System", "System"],
                ],
            })

            # SYNC_LOG
            updates.append({
                "range": f"{TAB_SYNC_LOG}!A1:I1",
                "values": [
                    ["Timestamp", "Tab", "Processed", "Inserted", "Updated",
                     "Skipped", "Rejected", "Status", "Error"],
                ],
            })

            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"valueInputOption": "RAW", "data": updates},
            ).execute()

            # ── Formula batchUpdate (USER_ENTERED) ───────────────────────────
            # DOC auto-fill and ABW auto-formula require USER_ENTERED input option.
            start_year = cycle.start_date.year if cycle.start_date else 2024
            start_month = cycle.start_date.month if cycle.start_date else 1
            start_day = cycle.start_date.day if cycle.start_date else 1
            doc_formula = (
                f'=ARRAYFORMULA(IF(A3:A500<>"", '
                f'INT(A3:A500 - DATE({start_year},{start_month},{start_day})) + 1, ""))'
            )
            formula_updates = [
                # DAILY_LOG: DOC auto-fill in B3
                {"range": f"{TAB_DAILY_LOG}!B3", "values": [[doc_formula]]},
                # DAILY_LOG: Status column in T3
                {"range": f"{TAB_DAILY_LOG}!T1", "values": [["Status"]]},
                {
                    "range": f"{TAB_DAILY_LOG}!T3",
                    "values": [[
                        '=ARRAYFORMULA(IF(A3:A500="","",IF((A3:A500<>"")'
                        '*(E3:E500<>"")'
                        '*(F3:F500<>""),"Ready","Incomplete"))'
                    ]],
                },
                {
                    "range": f"{TAB_DAILY_LOG}!U3",
                    "values": [[
                        f'=ARRAYFORMULA(IF(A3:A500="","", "{TAB_DAILY_LOG}-"&ROW(A3:A500)))'
                    ]],
                },
                # ABW_SAMPLING: DOC auto-fill in B3
                {"range": f"{TAB_ABW_SAMPLING}!B3", "values": [[doc_formula]]},
                # ABW_SAMPLING: ABW auto-formula in E3 (Total Weight / Sample Count)
                {
                    "range": f"{TAB_ABW_SAMPLING}!E3",
                    "values": [[
                        '=ARRAYFORMULA(IF((D3:D500<>"")*(C3:C500<>""),'
                        'D3:D500/C3:C500,""))'
                    ]],
                },
                {
                    "range": f"{TAB_ABW_SAMPLING}!K3",
                    "values": [[
                        f'=ARRAYFORMULA(IF(A3:A500="","", "{TAB_ABW_SAMPLING}-"&ROW(A3:A500)))'
                    ]],
                },
                # MORTALITY: DOC auto-fill in B3
                {"range": f"{TAB_MORTALITY}!B3", "values": [[doc_formula]]},
                {
                    "range": f"{TAB_MORTALITY}!E3",
                    "values": [[
                        f'=ARRAYFORMULA(IF(A3:A500="","", "{TAB_MORTALITY}-"&ROW(A3:A500)))'
                    ]],
                },
                {
                    "range": f"{TAB_COST}!J3",
                    "values": [[
                        f'=ARRAYFORMULA(IF(A3:A500="","", "{TAB_COST}-"&ROW(A3:A500)))'
                    ]],
                },
                {
                    "range": f"{TAB_HARVEST}!K3",
                    "values": [[
                        f'=ARRAYFORMULA(IF(A3:A500="","", "{TAB_HARVEST}-"&ROW(A3:A500)))'
                    ]],
                },
            ]
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"valueInputOption": "USER_ENTERED", "data": formula_updates},
            ).execute()

            # ── Formatting batchUpdate (freeze rows, validation, cond. format) ──
            format_requests = []
            # Freeze row 1 in all 7 tabs
            for tab_title, sid in sheet_id_map.items():
                format_requests.append({
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sid,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                })

            daily_sid = sheet_id_map.get(TAB_DAILY_LOG)
            cost_sid = sheet_id_map.get(TAB_COST)

            if daily_sid is not None:
                # Data validation: DO Average (col E=4), rows 3–500
                for col_idx, min_v, max_v, msg in [
                    (4,  0,  20,  "DO: 0–20 mg/L"),        # DO Average (E)
                    (7,  15, 45,  "Temp: 15–45 °C"),        # Temp Average (H)
                    (8,  0,  14,  "pH: 0–14"),              # pH Morning (I)
                    (9,  0,  14,  "pH: 0–14"),              # pH Afternoon (J)
                    (10, 0,  45,  "Salinity: 0–45 ppt"),    # Salinity (K)
                    (11, 0,  50,  "NH3: 0–50 mg/L"),        # NH3 (L)
                ]:
                    format_requests.append({
                        "setDataValidation": {
                            "range": {
                                "sheetId": daily_sid,
                                "startRowIndex": 2, "endRowIndex": 500,
                                "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1,
                            },
                            "rule": {
                                "condition": {
                                    "type": "NUMBER_BETWEEN",
                                    "values": [
                                        {"userEnteredValue": str(min_v)},
                                        {"userEnteredValue": str(max_v)},
                                    ],
                                },
                                "inputMessage": msg,
                                "strict": False,
                                "showCustomUi": True,
                            },
                        }
                    })

                # Conditional formatting: Status column T (col 19) — "Ready" → green
                format_requests.append({
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{
                                "sheetId": daily_sid,
                                "startRowIndex": 2, "endRowIndex": 500,
                                "startColumnIndex": 19, "endColumnIndex": 20,
                            }],
                            "booleanRule": {
                                "condition": {
                                    "type": "TEXT_EQ",
                                    "values": [{"userEnteredValue": "Ready"}],
                                },
                                "format": {"backgroundColor": {"red": 0.85, "green": 0.93, "blue": 0.83}},
                            },
                        },
                        "index": 0,
                    }
                })
                # "Incomplete" → yellow
                format_requests.append({
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{
                                "sheetId": daily_sid,
                                "startRowIndex": 2, "endRowIndex": 500,
                                "startColumnIndex": 19, "endColumnIndex": 20,
                            }],
                            "booleanRule": {
                                "condition": {
                                    "type": "TEXT_EQ",
                                    "values": [{"userEnteredValue": "Incomplete"}],
                                },
                                "format": {"backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.8}},
                            },
                        },
                        "index": 1,
                    }
                })

            if cost_sid is not None:
                # COST category dropdown (col B=1)
                format_requests.append({
                    "setDataValidation": {
                        "range": {
                            "sheetId": cost_sid,
                            "startRowIndex": 2, "endRowIndex": 500,
                            "startColumnIndex": 1, "endColumnIndex": 2,
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [
                                    {"userEnteredValue": v}
                                    for v in ["Benur", "Pakan", "Obat", "Listrik",
                                              "Tenaga Kerja", "Peralatan", "Lainnya"]
                                ],
                            },
                            "strict": False,
                            "showCustomUi": True,
                        },
                    }
                })
                # COST unit dropdown (col E=4)
                format_requests.append({
                    "setDataValidation": {
                        "range": {
                            "sheetId": cost_sid,
                            "startRowIndex": 2, "endRowIndex": 500,
                            "startColumnIndex": 4, "endColumnIndex": 5,
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [
                                    {"userEnteredValue": v}
                                    for v in ["kg", "L", "pcs", "ekor", "hari", "bulan", "unit"]
                                ],
                            },
                            "strict": False,
                            "showCustomUi": True,
                        },
                    }
                })

            if format_requests:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests": format_requests},
                ).execute()

            # Share with user
            if user_email:
                _share_spreadsheet(spreadsheet_id, user_email)

            # Auto-connect
            if user_id:
                existing = SheetIntegration.objects(cycle_id=cycle_id).first()
                if existing:
                    existing.spreadsheet_id = spreadsheet_id
                    existing.spreadsheet_url = spreadsheet_url
                    existing.is_active = True
                    existing.last_status = "pending"
                    existing.save()
                else:
                    SheetIntegration(
                        cycle_id=cycle_id,
                        user_id=user_id,
                        spreadsheet_id=spreadsheet_id,
                        spreadsheet_url=spreadsheet_url,
                    ).save()

            return 200, DataSuccessSchema(
                code=200,
                message="Template created",
                payload={
                    "spreadsheet_id": spreadsheet_id,
                    "spreadsheet_url": spreadsheet_url,
                    "cycle_id": cycle_id,
                    "auto_connected": bool(user_id),
                },
            )
        except Exception as exc:
            logger.exception("Template creation error: %s", exc)
            return 400, DataErrorSchema(code=400, message=str(exc))

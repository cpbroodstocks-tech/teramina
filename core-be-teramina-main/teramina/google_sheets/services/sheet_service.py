# pylint: disable=broad-except, too-many-branches, too-many-statements, too-many-locals

import logging
import os
from datetime import datetime, date as date_type

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.harvest.models.harvest_record_model import HarvestRecord
from teramina.cost_data.models.cost_data_model import CostData
from teramina.pond.models.pond_model import Pond
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema

from ..models.sheet_integration_model import SheetIntegration

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

# DAILY_LOG column layout (0-indexed):
# A=0  date          B=1  doc           C=2  do_morning     D=3  do_afternoon
# E=4  do_avg        F=5  temp_morning  G=6  temp_afternoon H=7  temp_avg
# I=8  ph_morning    J=9  ph_afternoon  K=10 salinity       L=11 nh3
# M=12 turbidity     N=13 feed_given_kg O=14 feed_leftover  P=15 feed_type
# Q=16 protein_pct   R=17 feeding_freq  S=18 notes


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
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])
    except HttpError as exc:
        logger.error("Sheets read error for %s/%s: %s", spreadsheet_id, range_name, exc)
        return []


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
    return s  # keep raw so at least the row isn't silently lost


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
            },
        )

    @staticmethod
    def sync_cycle(cycle_id: str) -> dict:
        """
        Pull data from all tabs and upsert into MongoDB.
        Returns summary dict: { tab: { inserted, updated, skipped, rejected } }
        """
        integration = SheetIntegration.objects(cycle_id=cycle_id, is_active=True).first()
        if not integration:
            return {"error": "No active integration found"}

        cycle = Cycle.objects(id=cycle_id).first()
        if not cycle:
            integration.last_status = "error"
            integration.last_error = "Cycle not found"
            integration.save()
            return {"error": "Cycle not found"}

        spreadsheet_id = integration.spreadsheet_id
        start_date = cycle.start_date
        summary = {}
        total_inserted = 0
        total_updated = 0

        try:
            service = _get_sheets_service()
        except Exception as exc:
            integration.last_status = "error"
            integration.last_error = str(exc)
            integration.save()
            return {"error": str(exc)}

        # ── DAILY_LOG ─────────────────────────────────────────────────────────
        try:
            rows = _get_sheet_values(service, spreadsheet_id, f"{TAB_DAILY_LOG}!A3:S")
            inserted = updated = skipped = rejected = 0

            cycle_data = CycleData.objects(cycle_id=cycle_id).first()
            existing_dates = {}
            if cycle_data and cycle_data.result_data:
                existing_dates = {
                    str(r.get("date", "")): i
                    for i, r in enumerate(cycle_data.result_data)
                }

            new_or_updated = []
            for row in rows:
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                if not date_str:
                    rejected += 1
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
                ph_morning = _safe_float(_col(row, 8))
                ph_afternoon = _safe_float(_col(row, 9))

                entry = {
                    "date": date_str,
                    "doc": doc,
                    "do_morning": do_morning,
                    "do_afternoon": do_afternoon,
                    "do_avg": do_avg,
                    "temp_morning": temp_morning,
                    "temp_afternoon": temp_afternoon,
                    "temp_avg": temp_avg,
                    "ph_morning": ph_morning,
                    "ph_afternoon": ph_afternoon,
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

                if date_str in existing_dates:
                    updated += 1
                else:
                    inserted += 1
                new_or_updated.append(entry)

            if new_or_updated:
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
                        # Update feed_leftover if now available
                        if fe.get("feed_leftover") is not None:
                            FeedRealization.objects(
                                cycle_id=cycle_id, doc=doc_val
                            ).update_one(
                                set__feed_leftover=fe["feed_leftover"],
                                set__last_updated=datetime.utcnow(),
                            )
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

            total_inserted += inserted
            total_updated += updated
            summary[TAB_DAILY_LOG] = {
                "inserted": inserted, "updated": updated,
                "skipped": skipped, "rejected": rejected,
            }
            _append_sync_log(service, spreadsheet_id, TAB_DAILY_LOG,
                             inserted + updated + skipped + rejected,
                             inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("DAILY_LOG sync error: %s", exc)
            summary[TAB_DAILY_LOG] = {"error": str(exc)}
            _append_sync_log(service, spreadsheet_id, TAB_DAILY_LOG,
                             0, 0, 0, 0, 0, "error", str(exc))

        # ── ABW_SAMPLING ──────────────────────────────────────────────────────
        try:
            rows = _get_sheet_values(service, spreadsheet_id, f"{TAB_ABW_SAMPLING}!A3:J")
            inserted = updated = skipped = rejected = 0

            cycle_data = CycleData.objects(cycle_id=cycle_id).first()
            existing_abw_dates = set()
            if cycle_data and cycle_data.result_data:
                existing_abw_dates = {
                    str(r.get("date", ""))
                    for r in cycle_data.result_data
                    if r.get("abw") is not None
                }

            new_abw = []
            for row in rows:
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                if not date_str:
                    rejected += 1
                    continue
                abw_val = _safe_float(_col(row, 4))
                if abw_val is None:
                    rejected += 1
                    continue

                doc = _safe_int(_col(row, 1)) or _auto_fill_doc(date_str, start_date)
                entry = {
                    "date": date_str,
                    "doc": doc,
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
                if date_str in existing_abw_dates:
                    updated += 1
                else:
                    inserted += 1
                new_abw.append(entry)

            if new_abw:
                _upsert_result_data(cycle_data, cycle_id, new_abw)

            total_inserted += inserted
            total_updated += updated
            summary[TAB_ABW_SAMPLING] = {
                "inserted": inserted, "updated": updated,
                "skipped": skipped, "rejected": rejected,
            }
            _append_sync_log(service, spreadsheet_id, TAB_ABW_SAMPLING,
                             inserted + updated + skipped + rejected,
                             inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("ABW_SAMPLING sync error: %s", exc)
            summary[TAB_ABW_SAMPLING] = {"error": str(exc)}
            _append_sync_log(service, spreadsheet_id, TAB_ABW_SAMPLING,
                             0, 0, 0, 0, 0, "error", str(exc))

        # ── COST ──────────────────────────────────────────────────────────────
        try:
            rows = _get_sheet_values(service, spreadsheet_id, f"{TAB_COST}!A3:I")
            inserted = skipped = rejected = 0

            cost_doc = CostData.objects(farm_id=cycle_id).first()
            existing_keys = set()
            if cost_doc and cost_doc.data:
                existing_keys = {
                    f"{r.get('date')}_{r.get('category')}_{r.get('description')}"
                    for r in cost_doc.data
                }

            new_costs = []
            for row in rows:
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                if not date_str:
                    rejected += 1
                    continue
                category = _safe_str(_col(row, 1))
                description = _safe_str(_col(row, 2))
                key = f"{date_str}_{category}_{description}"
                if key in existing_keys:
                    skipped += 1
                    continue
                entry = {
                    "date": date_str,
                    "category": category,
                    "description": description,
                    "quantity": _safe_float(_col(row, 3)),
                    "unit": _safe_str(_col(row, 4)),
                    "unit_price": _safe_float(_col(row, 5)),
                    "total": _safe_float(_col(row, 6)),
                    "vendor": _safe_str(_col(row, 7)),
                    "notes": _safe_str(_col(row, 8)),
                    "source": "google_sheets",
                }
                new_costs.append(entry)
                existing_keys.add(key)
                inserted += 1

            if new_costs:
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
            summary[TAB_COST] = {"inserted": inserted, "skipped": skipped, "rejected": rejected}
            _append_sync_log(service, spreadsheet_id, TAB_COST,
                             inserted + skipped + rejected, inserted, 0, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("COST sync error: %s", exc)
            summary[TAB_COST] = {"error": str(exc)}
            _append_sync_log(service, spreadsheet_id, TAB_COST,
                             0, 0, 0, 0, 0, "error", str(exc))

        # ── HARVEST ───────────────────────────────────────────────────────────
        try:
            rows = _get_sheet_values(service, spreadsheet_id, f"{TAB_HARVEST}!A3:J")
            inserted = updated = skipped = rejected = 0

            existing_harvest = HarvestRecord.objects(cycle_id=cycle_id)
            existing_harvest_dates = {
                str(r.harvest_data.get("date", "")) for r in existing_harvest
            }

            new_harvest = []
            for row in rows:
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                if not date_str:
                    rejected += 1
                    continue
                biomass = _safe_float(_col(row, 3))
                if biomass is None:
                    rejected += 1
                    continue

                doc = _safe_int(_col(row, 1)) or _auto_fill_doc(date_str, start_date)
                is_partial_raw = _safe_str(_col(row, 2)).upper()
                is_partial = is_partial_raw in ("Y", "YES", "1", "TRUE")

                harvest_data = {
                    "date": date_str,
                    "doc": doc,
                    "is_partial": is_partial,
                    "harvest_biomass_kg": biomass,
                    "abw_g": _safe_float(_col(row, 4)),
                    "sr_pct": _safe_float(_col(row, 5)),
                    "bags": _safe_int(_col(row, 6)),
                    "buyer": _safe_str(_col(row, 7)),
                    "price_per_kg_idr": _safe_float(_col(row, 8)),
                    "notes": _safe_str(_col(row, 9)),
                    "source": "google_sheets",
                }

                if date_str in existing_harvest_dates:
                    HarvestRecord.objects(
                        cycle_id=cycle_id,
                        **{"harvest_data__date": date_str}
                    ).update_one(set__harvest_data=harvest_data, set__last_updated=datetime.utcnow())
                    updated += 1
                else:
                    new_harvest.append(harvest_data)
                    existing_harvest_dates.add(date_str)
                    inserted += 1

            for hd in new_harvest:
                HarvestRecord(
                    cycle_id=cycle_id,
                    harvest_data=hd,
                    last_updated=datetime.utcnow(),
                ).save()

            total_inserted += inserted
            total_updated += updated
            summary[TAB_HARVEST] = {
                "inserted": inserted, "updated": updated,
                "skipped": skipped, "rejected": rejected,
            }
            _append_sync_log(service, spreadsheet_id, TAB_HARVEST,
                             inserted + updated + skipped + rejected,
                             inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("HARVEST sync error: %s", exc)
            summary[TAB_HARVEST] = {"error": str(exc)}
            _append_sync_log(service, spreadsheet_id, TAB_HARVEST,
                             0, 0, 0, 0, 0, "error", str(exc))

        # ── MORTALITY ─────────────────────────────────────────────────────────
        try:
            rows = _get_sheet_values(service, spreadsheet_id, f"{TAB_MORTALITY}!A3:D")
            inserted = updated = skipped = rejected = 0

            mortality_rows = []
            for row in rows:
                if not row or not _col(row, 0):
                    continue
                date_str = _normalize_date(_col(row, 0))
                if not date_str:
                    rejected += 1
                    continue
                dead_count = _safe_int(_col(row, 2))
                if dead_count is None:
                    rejected += 1
                    continue

                doc = _safe_int(_col(row, 1)) or _auto_fill_doc(date_str, start_date)
                entry = {
                    "date": date_str,
                    "doc": doc,
                    "mortality_count": dead_count,
                    "mortality_notes": _safe_str(_col(row, 3)),
                    "source": "google_sheets",
                }
                mortality_rows.append(entry)
                inserted += 1

            if mortality_rows:
                cycle_data = CycleData.objects(cycle_id=cycle_id).first()
                _upsert_result_data(cycle_data, cycle_id, mortality_rows)

            total_inserted += inserted
            summary[TAB_MORTALITY] = {
                "inserted": inserted, "updated": updated,
                "skipped": skipped, "rejected": rejected,
            }
            _append_sync_log(service, spreadsheet_id, TAB_MORTALITY,
                             inserted + updated + skipped + rejected,
                             inserted, updated, skipped, rejected, "ok")
        except Exception as exc:
            logger.exception("MORTALITY sync error: %s", exc)
            summary[TAB_MORTALITY] = {"error": str(exc)}
            _append_sync_log(service, spreadsheet_id, TAB_MORTALITY,
                             0, 0, 0, 0, 0, "error", str(exc))

        # ── Finalize ──────────────────────────────────────────────────────────
        had_error = any("error" in v for v in summary.values())
        all_tabs_ok = all("error" not in v for v in summary.values())
        integration.last_synced = datetime.utcnow()
        integration.last_status = "ok" if all_tabs_ok else ("partial" if not had_error else "error")
        integration.last_error = "; ".join(
            f"{k}: {v['error']}" for k, v in summary.items() if "error" in v
        ) or None
        integration.rows_synced = (integration.rows_synced or 0) + total_inserted + total_updated
        integration.save()

        return summary

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
                "range": f"{TAB_DAILY_LOG}!A1:S2",
                "values": [
                    ["Date", "DOC", "DO Morning", "DO Afternoon", "DO Average",
                     "Temp Morning", "Temp Afternoon", "Temp Average",
                     "pH Morning", "pH Afternoon", "Salinity", "NH3/Ammonia",
                     "Turbidity", "Feed Given", "Feed Leftover",
                     "Feed Type", "Protein %", "Feeding Freq", "Notes"],
                    ["YYYY-MM-DD", "days", "mg/L", "mg/L", "mg/L",
                     "°C", "°C", "°C",
                     "", "", "ppt", "mg/L",
                     "Secchi cm", "kg", "kg",
                     "", "%", "times/day", ""],
                ],
            })

            # ABW_SAMPLING
            updates.append({
                "range": f"{TAB_ABW_SAMPLING}!A1:J2",
                "values": [
                    ["Date", "DOC", "Sample Count", "Total Weight", "ABW",
                     "Min Weight", "Max Weight", "CV%", "Sampled By", "Notes"],
                    ["YYYY-MM-DD", "days", "shrimp", "g", "g (REQUIRED)",
                     "g", "g", "%", "", ""],
                ],
            })

            # MORTALITY
            updates.append({
                "range": f"{TAB_MORTALITY}!A1:D2",
                "values": [
                    ["Date", "DOC", "Dead Count", "Notes"],
                    ["YYYY-MM-DD", "days", "shrimp (REQUIRED)", ""],
                ],
            })

            # COST
            updates.append({
                "range": f"{TAB_COST}!A1:I2",
                "values": [
                    ["Date", "Category", "Description", "Quantity", "Unit",
                     "Unit Price (IDR)", "Total (IDR)", "Vendor", "Notes"],
                    ["YYYY-MM-DD", "Feed/Chemical/Labor/Electricity/Other",
                     "", "", "kg/L/pcs/day", "", "REQUIRED", "", ""],
                ],
            })

            # HARVEST
            updates.append({
                "range": f"{TAB_HARVEST}!A1:J2",
                "values": [
                    ["Date", "DOC", "Is Partial?", "Biomass (kg)", "ABW (g)",
                     "SR (%)", "Bags/Count", "Buyer", "Price/kg (IDR)", "Notes"],
                    ["YYYY-MM-DD", "days", "Y or N", "kg (REQUIRED)", "g",
                     "%", "", "", "", ""],
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

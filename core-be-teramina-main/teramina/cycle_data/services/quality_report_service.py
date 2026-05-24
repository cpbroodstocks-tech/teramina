# pylint: disable=broad-except
"""
Per-cycle data quality analysis.
Assesses completeness, gap windows, staleness, and physiological anomalies.
"""
import logging
from datetime import datetime, date, timedelta

import pandas as pd

from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.cycle_data.services.data_validator import validate_cycle_data

logger = logging.getLogger("teramina")

# Fields a row must have to count as "complete" for that day
REQUIRED_FIELDS = ["date", "do_avg", "temp_avg", "feed_given_kg"]
OPTIONAL_FIELDS = ["ph_morning", "salinity", "nh3", "turbidity", "abw"]

# A date gap is flagged when ≥ this many consecutive days have no data
GAP_THRESHOLD_DAYS = 2

# Alert raised when no data exists for this many trailing days
STALE_THRESHOLD_DAYS = 5


def get_quality_report(cycle_id: str) -> dict:
    """
    Build a data quality report for a cycle.

    Returns:
        dict with keys:
            completeness_by_doc: list of {doc, date, fields_filled, fields_required, completeness_pct}
            gap_windows: list of {from_doc, to_doc, days, from_date, to_date}
            stale_since: str date or None
            anomaly_count: int (hard failures from physiological validation)
            total_days_with_data: int
            total_days_in_cycle: int
            overall_completeness_pct: float
    """
    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return {"error": "Cycle not found"}

    cycle_data_doc = CycleData.objects(cycle_id=cycle_id).first()
    result_data = cycle_data_doc.result_data if cycle_data_doc else []

    start_dt = cycle.start_date
    if not start_dt:
        return {"error": "Cycle has no start_date"}
    if isinstance(start_dt, datetime):
        start_date_obj = start_dt.date()
    else:
        start_date_obj = start_dt

    today = date.today()
    total_days_in_cycle = (today - start_date_obj).days + 1

    # Build a date → merged-fields dict from all rows sharing that date
    date_map: dict = {}
    for row in result_data:
        row_date = row.get("date")
        if not row_date:
            continue
        # Normalize to string key
        if isinstance(row_date, (datetime, date)):
            key = row_date.strftime("%Y-%m-%d")
        else:
            key = str(row_date)[:10]
        if key not in date_map:
            date_map[key] = {}
        date_map[key].update({k: v for k, v in row.items() if v is not None and v != ""})

    # Build completeness_by_doc over the full cycle span
    completeness_by_doc = []
    gap_windows = []
    gap_start_doc = None
    gap_start_date = None
    total_days_with_data = 0

    for day_offset in range(total_days_in_cycle):
        current_date = start_date_obj + timedelta(days=day_offset)
        doc = day_offset + 1
        key = current_date.strftime("%Y-%m-%d")

        row = date_map.get(key, {})
        has_any_data = bool(row)

        if has_any_data:
            total_days_with_data += 1
            # Close any open gap
            if gap_start_doc is not None:
                gap_days = doc - gap_start_doc
                if gap_days >= GAP_THRESHOLD_DAYS:
                    gap_windows.append({
                        "from_doc": gap_start_doc,
                        "to_doc": doc - 1,
                        "days": gap_days,
                        "from_date": gap_start_date,
                        "to_date": (current_date - timedelta(days=1)).strftime("%Y-%m-%d"),
                    })
                gap_start_doc = None
                gap_start_date = None

            filled = sum(1 for f in REQUIRED_FIELDS if row.get(f) not in (None, ""))
            pct = round(filled / len(REQUIRED_FIELDS) * 100, 1)
        else:
            # Open or extend gap
            if gap_start_doc is None:
                gap_start_doc = doc
                gap_start_date = key
            filled = 0
            pct = 0.0

        completeness_by_doc.append({
            "doc": doc,
            "date": key,
            "fields_filled": filled,
            "fields_required": len(REQUIRED_FIELDS),
            "completeness_pct": pct,
        })

    # Close trailing gap
    if gap_start_doc is not None:
        gap_days = total_days_in_cycle - gap_start_doc + 1
        if gap_days >= GAP_THRESHOLD_DAYS:
            gap_windows.append({
                "from_doc": gap_start_doc,
                "to_doc": total_days_in_cycle,
                "days": gap_days,
                "from_date": gap_start_date,
                "to_date": today.strftime("%Y-%m-%d"),
            })

    # Stale check: find the last date with any data
    stale_since = None
    if date_map:
        last_data_date = max(date_map.keys())
        days_since = (today - datetime.strptime(last_data_date, "%Y-%m-%d").date()).days
        if days_since >= STALE_THRESHOLD_DAYS:
            stale_since = last_data_date
    elif total_days_in_cycle > 0:
        stale_since = start_date_obj.strftime("%Y-%m-%d")

    # Anomaly count via physiological validation
    anomaly_count = 0
    if result_data:
        try:
            df = pd.DataFrame(result_data)
            # Rename to match validator expectations
            rename = {}
            if "do_avg" in df.columns:
                rename["do_avg"] = "do"
            if "temp_avg" in df.columns:
                rename["temp_avg"] = "temperature"
            val_df = df.rename(columns=rename)
            report = validate_cycle_data(val_df)
            anomaly_count = len(report.hard_failures)
        except Exception as exc:
            logger.warning("Quality report validation error: %s", exc)

    overall_completeness_pct = 0.0
    if completeness_by_doc:
        all_pcts = [r["completeness_pct"] for r in completeness_by_doc]
        overall_completeness_pct = round(sum(all_pcts) / len(all_pcts), 1)

    return {
        "completeness_by_doc": completeness_by_doc,
        "gap_windows": gap_windows,
        "stale_since": stale_since,
        "anomaly_count": anomaly_count,
        "total_days_with_data": total_days_with_data,
        "total_days_in_cycle": total_days_in_cycle,
        "overall_completeness_pct": overall_completeness_pct,
    }

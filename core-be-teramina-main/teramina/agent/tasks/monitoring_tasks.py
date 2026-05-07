# pylint: disable=broad-except

import logging
from datetime import datetime, timedelta
from celery import shared_task

from teramina.cycle.models.cycle_model import Cycle
from teramina.pond.models.pond_model import Pond
from teramina.farm.models.farm_model import Farm
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData
from teramina.helpers.constant_value import Constant
from teramina.helpers.fcm_helper import notify_user_alert
from ..models.agent_model import FarmAlert

logger = logging.getLogger("teramina")


def _get_user_id_for_cycle(cycle_id: str) -> str | None:
    """Resolve user_id from cycle → pond → farm."""
    cycle = Cycle.objects(id=cycle_id).first()
    if not cycle:
        return None
    pond = Pond.objects(id=cycle.pond_id).first()
    if not pond:
        return None
    farm = Farm.objects(id=pond.farm_id).first()
    return str(farm.user_id) if farm else None


def _save_alert(user_id: str, farm_id: str, cycle_id: str,
                alert_type: str, severity: str, message: str, data: dict) -> None:
    """Save an alert if an identical un-read alert doesn't already exist from last 24h."""
    cutoff = datetime.utcnow() - timedelta(hours=24)
    existing = FarmAlert.objects(
        cycle_id=cycle_id,
        alert_type=alert_type,
        is_read=False,
        created_at__gte=cutoff,
    ).first()
    if existing:
        return  # suppress duplicate within 24h
    FarmAlert(
        user_id=user_id,
        farm_id=farm_id,
        cycle_id=cycle_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        data=data,
        expires_at=datetime.utcnow() + timedelta(days=7),
    ).save()
    notify_user_alert(user_id, alert_type, severity, message, cycle_id)


@shared_task(name="agent.monitor_all_active_cycles")
def monitor_all_active_cycles():
    """
    Celery Beat task (every 6 hours): evaluate all active cycles and generate alerts.
    """
    active_cycles = Cycle.objects(is_active=True).only("id", "pond_id")
    generated = 0
    errors = 0

    for cycle in active_cycles:
        try:
            cycle_id = str(cycle.id)
            pond = Pond.objects(id=cycle.pond_id).first()
            if not pond:
                continue
            farm = Farm.objects(id=pond.farm_id).first()
            if not farm:
                continue

            user_id = str(farm.user_id)
            farm_id = str(farm.id)

            cd = CycleData.objects(cycle_id=cycle_id).first()
            if not cd or not cd.result_data:
                continue

            data = cd.result_data
            recent = sorted(
                [r for r in data if r.get("doc")], key=lambda x: x["doc"]
            )[-3:]

            # ── Water quality checks ──────────────────────────────────────────
            do_vals = [r["do_avg"] for r in recent if r.get("do_avg")]
            nh3_vals = [r["nh3"] for r in recent if r.get("nh3")]

            if do_vals:
                avg_do = sum(do_vals) / len(do_vals)
                if avg_do < Constant.DO_SUITABLE_MIN:
                    _save_alert(
                        user_id, farm_id, cycle_id,
                        "water_quality", "critical",
                        f"DO critical: {avg_do:.1f} mg/L (below survival minimum {Constant.DO_SUITABLE_MIN})",
                        {"do_avg_3d": avg_do},
                    )
                    generated += 1
                elif avg_do < Constant.DO_OPTIMAL_MIN:
                    _save_alert(
                        user_id, farm_id, cycle_id,
                        "water_quality", "warning",
                        f"DO below optimal: {avg_do:.1f} mg/L (optimal ≥{Constant.DO_OPTIMAL_MIN})",
                        {"do_avg_3d": avg_do},
                    )
                    generated += 1

            if nh3_vals:
                avg_nh3 = sum(nh3_vals) / len(nh3_vals)
                if avg_nh3 > Constant.NH3_SUITABLE_MAX * 0.8:
                    _save_alert(
                        user_id, farm_id, cycle_id,
                        "water_quality", "critical",
                        f"NH3 dangerously high: {avg_nh3:.3f} mg/L (limit {Constant.NH3_SUITABLE_MAX})",
                        {"nh3_avg_3d": avg_nh3},
                    )
                    generated += 1
                elif avg_nh3 > Constant.NH3_OPTIMAL_MAX:
                    _save_alert(
                        user_id, farm_id, cycle_id,
                        "water_quality", "warning",
                        f"NH3 elevated: {avg_nh3:.3f} mg/L (optimal ≤{Constant.NH3_OPTIMAL_MAX})",
                        {"nh3_avg_3d": avg_nh3},
                    )
                    generated += 1

            # ── Harvest window check ──────────────────────────────────────────
            fd = ForecastData.objects(cycle_id=cycle_id).first()
            if fd and fd.result_data:
                docs_now = [r.get("doc") for r in data if r.get("doc")]
                current_doc = max(docs_now) if docs_now else 0
                # Find optimal harvest DOC
                best_profit = float("-inf")
                best_doc = None
                for row in fd.result_data:
                    profit = row.get("profit") or row.get("forecasted_profit") or 0
                    if profit > best_profit:
                        best_profit = profit
                        best_doc = row.get("doc")

                if best_doc and 0 < best_doc - current_doc <= 7:
                    _save_alert(
                        user_id, farm_id, cycle_id,
                        "harvest_window", "info",
                        f"Optimal harvest window opens in {best_doc - current_doc} days (DOC {best_doc})",
                        {"optimal_doc": best_doc, "current_doc": current_doc},
                    )
                    generated += 1

        except Exception as exc:
            logger.error("Monitoring error for cycle %s: %s", str(cycle.id), exc)
            errors += 1

    logger.info("Monitoring complete: %d alerts generated, %d errors", generated, errors)
    return {"generated": generated, "errors": errors}

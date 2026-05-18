# pylint: disable=broad-except

import logging
import math
from datetime import datetime, timedelta
from celery import shared_task

from teramina.cycle.models.cycle_model import Cycle
from teramina.pond.models.pond_model import Pond
from teramina.farm.models.farm_model import Farm
from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData
from teramina.cost_data.models.cost_data_model import CostData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.helpers.constant_value import Constant
from teramina.helpers.fcm_helper import notify_user_alert
from ..models.agent_model import FarmAlert, WorkflowTask

_COST_PER_KG_BENCHMARK_IDR = 25_000  # IDR/kg baseline; alert when >20% above this

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
    alert = FarmAlert(
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

    if severity == "critical":
        existing_task = WorkflowTask.objects(
            user_id=user_id,
            cycle_id=cycle_id,
            is_completed=False,
            created_at__gte=cutoff,
        ).first()
        if not existing_task:
            task = WorkflowTask(
                user_id=user_id,
                farm_id=farm_id,
                cycle_id=cycle_id,
                task_type="check",
                title=message[:80],
                description=f"Critical {alert_type} alert — verify and take action",
                due_at=datetime.utcnow() + timedelta(hours=6),
                source_alert_id=str(alert.id),
                created_at=datetime.utcnow(),
            ).save()
            alert.follow_up_task_id = str(task.id)
            alert.save()


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

            # ── NH3 rising trend (3 consecutive days rising) ─────────────────
            all_nh3 = sorted(
                [(r.get("doc"), r.get("nh3")) for r in data if r.get("doc") and r.get("nh3")],
                key=lambda x: x[0],
            )
            if len(all_nh3) >= 3:
                last3_nh3 = [v for _, v in all_nh3[-3:]]
                if last3_nh3[0] < last3_nh3[1] < last3_nh3[2]:
                    _save_alert(
                        user_id, farm_id, cycle_id,
                        "water_quality", "warning",
                        f"NH3 rising for 3 consecutive days: {last3_nh3[0]:.3f} → {last3_nh3[1]:.3f} → {last3_nh3[2]:.3f} mg/L",
                        {"nh3_trend": last3_nh3},
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

            # ── Feed leftover > 20% ───────────────────────────────────────────
            recent_feed = list(FeedRealization.objects(cycle_id=cycle_id).order_by("-doc").limit(7))
            if recent_feed:
                total_given = sum(r.feed_given or 0 for r in recent_feed)
                total_leftover = sum(r.feed_leftover or 0 for r in recent_feed)
                if total_given > 0:
                    leftover_pct = total_leftover / total_given * 100
                    if leftover_pct > 20:
                        _save_alert(
                            user_id, farm_id, cycle_id,
                            "feeding", "info",
                            f"Feed leftover rate high: {leftover_pct:.1f}% in last 7 days — consider reducing feed by 10–15%",
                            {"leftover_pct_7d": round(leftover_pct, 1), "total_given_kg": round(total_given, 2)},
                        )
                        generated += 1

            # ── Growth lag after DOC 45 ───────────────────────────────────────
            docs_now = [r.get("doc") for r in data if r.get("doc")]
            current_doc_val = max(docs_now) if docs_now else 0
            if current_doc_val > 45:
                abw_rows = sorted(
                    [(r["doc"], r["abw"]) for r in data if r.get("abw") and r.get("doc")],
                    key=lambda x: x[0],
                )
                if len(abw_rows) >= 2:
                    d1, w1 = abw_rows[-2]
                    d2, w2 = abw_rows[-1]
                    if w1 > 0 and w2 > 0 and d2 > d1:
                        sgr = (math.log(w2) - math.log(w1)) / (d2 - d1) * 100
                        expected_sgr = 3.5
                        if sgr < expected_sgr:
                            _save_alert(
                                user_id, farm_id, cycle_id,
                                "growth", "warning",
                                f"Growth lag at DOC {current_doc_val}: SGR {sgr:.2f}%/day (expected ≥{expected_sgr}%/day). Check feeding, water quality, and stocking density.",
                                {"current_doc": current_doc_val, "sgr_pct_day": round(sgr, 3), "expected_sgr": expected_sgr},
                            )
                            generated += 1

            # ── Cost/kg exceeding benchmark ───────────────────────────────────
            cost_doc = CostData.objects(farm_id=farm_id).first()
            if cost_doc and cost_doc.data:
                total_cost = sum(r.get("total", 0) or 0 for r in cost_doc.data)
                biomass_rows = [
                    (r.get("doc"), r.get("biomass") or r.get("pond_biomass"))
                    for r in data
                    if r.get("doc") and (r.get("biomass") or r.get("pond_biomass"))
                ]
                if biomass_rows and total_cost > 0:
                    latest_biomass = sorted(biomass_rows, key=lambda x: x[0])[-1][1]
                    if latest_biomass and latest_biomass > 0:
                        cost_per_kg = total_cost / latest_biomass
                        if cost_per_kg > _COST_PER_KG_BENCHMARK_IDR * 1.2:
                            _save_alert(
                                user_id, farm_id, cycle_id,
                                "cost", "info",
                                f"Cost/kg above benchmark: Rp{cost_per_kg:,.0f}/kg (benchmark Rp{_COST_PER_KG_BENCHMARK_IDR:,}/kg). Review feed and operational costs.",
                                {"cost_per_kg_idr": round(cost_per_kg, 0), "benchmark_idr": _COST_PER_KG_BENCHMARK_IDR},
                            )
                            generated += 1

        except Exception as exc:
            logger.error("Monitoring error for cycle %s: %s", str(cycle.id), exc)
            errors += 1

    logger.info("Monitoring complete: %d alerts generated, %d errors", generated, errors)
    return {"generated": generated, "errors": errors}


@shared_task(name="agent.weekly_farm_summary")
def weekly_farm_summary():
    """
    Celery Beat task (weekly): create a summary WorkflowTask for each farm owner
    listing active cycles, key metrics, and any unresolved alerts from the past 7 days.
    """
    from teramina.farm.models.farm_model import Farm
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=7)
    farms = Farm.objects()
    created = 0
    errors = 0

    for farm in farms:
        try:
            farm_id = str(farm.id)
            user_id = str(farm.user_id)

            active_cycles = Cycle.objects(is_active=True)
            cycle_ids = []
            for cycle in active_cycles:
                pond = Pond.objects(id=cycle.pond_id).first()
                if pond and str(pond.farm_id) == farm_id:
                    cycle_ids.append(str(cycle.id))

            if not cycle_ids:
                continue

            unresolved = FarmAlert.objects(
                user_id=user_id, farm_id=farm_id,
                is_read=False, created_at__gte=cutoff,
            ).count()

            lines = [f"Weekly summary — {farm.name}"]
            lines.append(f"Active cycles: {len(cycle_ids)}")
            if unresolved:
                lines.append(f"Unresolved alerts (7d): {unresolved} — review in the Today view")

            for cycle_id in cycle_ids[:3]:
                cd = CycleData.objects(cycle_id=cycle_id).first()
                if cd and cd.result_data:
                    rows = sorted(
                        [r for r in cd.result_data if r.get("doc")],
                        key=lambda x: x["doc"],
                    )
                    if rows:
                        last = rows[-1]
                        doc = last.get("doc", "?")
                        do_val = last.get("do_avg", "?")
                        abw = last.get("abw", "?")
                        lines.append(f"  Cycle {cycle_id[:8]}: DOC {doc}, DO {do_val} mg/L, ABW {abw}g")

            existing_task = WorkflowTask.objects(
                user_id=user_id, farm_id=farm_id, task_type="reminder",
                created_at__gte=cutoff,
                title__startswith="Weekly summary",
            ).first()
            if existing_task:
                continue

            WorkflowTask(
                user_id=user_id,
                farm_id=farm_id,
                task_type="reminder",
                title=f"Weekly summary — {farm.name}",
                description="\n".join(lines),
                due_at=datetime.utcnow() + timedelta(days=1),
                created_at=datetime.utcnow(),
            ).save()
            created += 1

        except Exception as exc:
            logger.error("weekly_farm_summary error for farm %s: %s", str(farm.id), exc)
            errors += 1

    logger.info("Weekly summary complete: %d tasks created, %d errors", created, errors)
    return {"created": created, "errors": errors}

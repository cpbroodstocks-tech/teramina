# pylint: disable=broad-except, too-many-locals, too-many-branches

import json
import logging
import os
from datetime import datetime

import anthropic

from teramina.cycle_data.models.cycle_data_model import CycleData, ForecastData
from teramina.cost_data.models.cost_data_model import CostData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.cycle.models.cycle_model import Cycle
from teramina.pond.models.pond_model import Pond
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from ..models.insight_model import CycleInsightCache

logger = logging.getLogger("teramina")

VALID_TYPES = {"performance", "water_quality", "feeding", "harvest", "economics", "weekly"}


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def _build_cycle_context(cycle_id: str) -> dict:
    """Assemble all available cycle data into a context dict for the LLM."""
    context = {"cycle_id": cycle_id}

    cycle = Cycle.objects(id=cycle_id).first()
    if cycle:
        context["cycle_name"] = cycle.name
        context["start_date"] = cycle.start_date.isoformat() if cycle.start_date else None

    cycle_data = CycleData.objects(cycle_id=cycle_id).first()
    if cycle_data and cycle_data.result_data:
        data = cycle_data.result_data
        context["total_data_points"] = len(data)

        # Get current DOC
        docs = [r.get("doc") for r in data if r.get("doc")]
        context["current_doc"] = max(docs) if docs else 0

        # Latest ABW
        abw_data = [(r.get("doc"), r.get("abw")) for r in data if r.get("abw")]
        if abw_data:
            abw_data.sort(key=lambda x: x[0])
            context["latest_abw_g"] = abw_data[-1][1]
            context["abw_history"] = abw_data[-10:]  # last 10 samples

        # Recent water quality (last 7 days)
        recent = sorted(
            [r for r in data if r.get("doc") and r.get("do_avg")],
            key=lambda x: x["doc"]
        )[-7:]
        if recent:
            context["recent_wq"] = [
                {
                    "doc": r.get("doc"),
                    "do_avg": r.get("do_avg"),
                    "temp_avg": r.get("temp_avg"),
                    "nh3": r.get("nh3"),
                    "ph_morning": r.get("ph_morning"),
                    "salinity": r.get("salinity"),
                }
                for r in recent
            ]

        # Feed given trend (last 7 days)
        feed_recent = sorted(
            [r for r in data if r.get("doc") and r.get("feed_given_kg")],
            key=lambda x: x["doc"]
        )[-7:]
        if feed_recent:
            context["recent_feed"] = [
                {"doc": r["doc"], "feed_given_kg": r["feed_given_kg"]}
                for r in feed_recent
            ]

    # Forecast data
    forecast_doc = ForecastData.objects(cycle_id=cycle_id).first()
    if forecast_doc and forecast_doc.result_data:
        forecast = forecast_doc.result_data
        # Find harvest window (peak profit DOC)
        best = max(forecast, key=lambda x: float(x.get("profit", 0) or 0), default=None)
        if best:
            context["forecast_optimal_doc"] = best.get("doc")
            context["forecast_optimal_biomass"] = best.get("biomass") or best.get("pond_biomass")
        context["forecast_final_abw"] = forecast[-1].get("abw") if forecast else None
        context["forecast_final_sr"] = forecast[-1].get("sr") or forecast[-1].get("survival_rate") if forecast else None

    # Cost data
    cost_doc = CostData.objects(farm_id=cycle_id).first()
    if cost_doc and cost_doc.data:
        total_cost = sum(r.get("total", 0) or 0 for r in cost_doc.data)
        context["total_cost_idr"] = total_cost
        # Breakdown by category
        by_cat: dict = {}
        for r in cost_doc.data:
            cat = r.get("category", "other")
            by_cat[cat] = by_cat.get(cat, 0) + (r.get("total", 0) or 0)
        context["cost_breakdown"] = by_cat

    # FCR estimate
    if context.get("total_cost_idr") and context.get("latest_abw_g") and context.get("current_doc"):
        feed_total = sum(
            r.get("feed_given_kg", 0) or 0
            for r in (cycle_data.result_data if cycle_data else [])
        )
        # Rough biomass estimate
        abw = context.get("latest_abw_g", 0)
        # FCR = total_feed / biomass_harvested (approximate)
        context["total_feed_given_kg"] = feed_total

    return context


def _build_prompt(insight_type: str, context: dict) -> str:
    """Build the user prompt for a specific insight type."""
    context_json = json.dumps(context, indent=2, default=str)

    type_instructions = {
        "performance": "Analyze overall cycle performance: growth rate, survival, FCR trend, and whether the cycle is on track.",
        "water_quality": "Analyze water quality trends: DO, temperature, NH3, pH, salinity. Identify any stress periods and their impact on growth.",
        "feeding": "Analyze feeding efficiency: feed given vs recommended, leftover trends, FCR trajectory, and cost of feeding.",
        "harvest": "Analyze harvest readiness: current ABW vs target, optimal harvest window, revenue projection.",
        "economics": "Analyze economics: cost breakdown, cost per kg trend, revenue forecast, profit projection.",
        "weekly": "Generate a concise weekly summary covering all key metrics, notable events, and recommendations for next week.",
    }

    instruction = type_instructions.get(insight_type, type_instructions["performance"])

    return f"""You are an expert shrimp aquaculture analyst for Teramina, a farm management platform.

Analyze the following cycle data and generate a structured JSON insight.

Insight type: {insight_type}
Instruction: {instruction}

Cycle data:
{context_json}

Return ONLY valid JSON with this exact structure:
{{
  "summary": "2-3 sentence executive summary",
  "performance_score": <integer 0-100>,
  "metrics": [
    {{
      "name": "<metric name>",
      "current_value": <number or null>,
      "target_value": <number or null>,
      "unit": "<unit string>",
      "status": "<good|warning|critical>",
      "trend": "<improving|stable|declining>",
      "insight": "<one sentence>"
    }}
  ],
  "anomalies": [
    {{
      "type": "<water_quality|growth|feeding|economics>",
      "severity": "<low|medium|high>",
      "description": "<what happened>",
      "first_detected_doc": <integer or null>,
      "recommendation": "<what to do>"
    }}
  ],
  "recommendations": [
    {{
      "priority": "<urgent|soon|monitor>",
      "action": "<what to do>",
      "reason": "<why>",
      "expected_impact": "<what improvement to expect>"
    }}
  ],
  "forecast_outlook": "<1-2 sentence outlook for next 2 weeks>"
}}

Rules:
- Be specific with numbers from the data. Do not invent values not present in the data.
- If data is missing, set the value to null and note it in the insight field.
- performance_score: 0=catastrophic, 50=average, 80=good, 100=excellent
- Only include anomalies that are genuinely present in the data
- Limit to 3 most important recommendations
- Respond in English unless the cycle name suggests Indonesian (then use Indonesian)"""


# ── Tool implementations for stream_insight ──────────────────────────────────

def _tool_get_growth_metrics(cycle_id: str) -> dict:
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No cycle data found"}

    data = cd.result_data
    docs = [r.get("doc") for r in data if r.get("doc")]
    current_doc = max(docs) if docs else 0

    abw_rows = sorted(
        [(r["doc"], r["abw"]) for r in data if r.get("abw")],
        key=lambda x: x[0]
    )
    latest_abw = abw_rows[-1][1] if abw_rows else None
    abw_history = abw_rows[-10:] if abw_rows else []

    # Simple ADG estimate from last two ABW readings
    adg_estimate = None
    if len(abw_rows) >= 2:
        (doc1, abw1), (doc2, abw2) = abw_rows[-2], abw_rows[-1]
        if doc2 != doc1:
            adg_estimate = round((abw2 - abw1) / (doc2 - doc1), 3)

    return {
        "current_doc": current_doc,
        "latest_abw_g": latest_abw,
        "abw_history": abw_history,
        "adg_estimate": adg_estimate,
    }


def _tool_get_water_quality(cycle_id: str, days: int = 7) -> dict:
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No cycle data found"}

    recent = sorted(
        [r for r in cd.result_data if r.get("doc")],
        key=lambda x: x["doc"]
    )[-days:]

    return {
        "days_requested": days,
        "readings": [
            {
                "doc": r.get("doc"),
                "do_avg": r.get("do_avg"),
                "temp_avg": r.get("temp_avg"),
                "nh3": r.get("nh3"),
                "ph_morning": r.get("ph_morning"),
                "salinity": r.get("salinity"),
            }
            for r in recent
        ],
    }


def _tool_get_feeding_summary(cycle_id: str) -> dict:
    cd = CycleData.objects(cycle_id=cycle_id).first()
    if not cd or not cd.result_data:
        return {"error": "No cycle data found"}

    data = cd.result_data
    total_feed = round(sum(r.get("feed_given_kg", 0) or 0 for r in data), 2)

    recent_feed = sorted(
        [r for r in data if r.get("doc") and r.get("feed_given_kg")],
        key=lambda x: x["doc"]
    )[-7:]

    # Rough FCR: total_feed / estimated_biomass_kg
    abw_rows = sorted(
        [(r["doc"], r["abw"]) for r in data if r.get("abw")],
        key=lambda x: x[0]
    )
    fcr_estimate = None
    if abw_rows and total_feed:
        # Biomass estimate using latest ABW (g) * assumed stocking density placeholder
        # We can only do feed/ABW ratio as a proxy; flag it as approximate
        latest_abw = abw_rows[-1][1]
        if latest_abw:
            fcr_estimate = round(total_feed / (latest_abw / 1000), 3) if latest_abw else None

    return {
        "total_feed_kg": total_feed,
        "recent_feed": [
            {"doc": r["doc"], "feed_given_kg": r["feed_given_kg"]}
            for r in recent_feed
        ],
        "fcr_estimate": fcr_estimate,
    }


def _tool_get_economics(cycle_id: str) -> dict:
    cost_doc = CostData.objects(farm_id=cycle_id).first()
    total_cost = 0
    cost_breakdown: dict = {}
    if cost_doc and cost_doc.data:
        total_cost = round(sum(r.get("total", 0) or 0 for r in cost_doc.data), 0)
        for r in cost_doc.data:
            cat = r.get("category", "other")
            cost_breakdown[cat] = cost_breakdown.get(cat, 0) + (r.get("total", 0) or 0)
        cost_breakdown = {k: round(v, 0) for k, v in cost_breakdown.items()}

    forecast_optimal_doc = None
    fd = ForecastData.objects(cycle_id=cycle_id).first()
    if fd and fd.result_data:
        best = max(fd.result_data, key=lambda x: float(x.get("profit", 0) or 0), default=None)
        if best:
            forecast_optimal_doc = best.get("doc")

    return {
        "total_cost_idr": total_cost,
        "cost_breakdown": cost_breakdown,
        "forecast_optimal_doc": forecast_optimal_doc,
    }


_INSIGHT_TOOL_DEFINITIONS = [
    {
        "name": "get_growth_metrics",
        "description": "Get growth metrics for the cycle: current DOC, latest ABW, ABW history, and ADG estimate.",
        "input_schema": {
            "type": "object",
            "properties": {"cycle_id": {"type": "string", "description": "Cycle ID"}},
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_water_quality",
        "description": "Get recent water quality readings (DO, temp, NH3, pH, salinity) for the last N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string"},
                "days": {"type": "integer", "default": 7},
            },
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_feeding_summary",
        "description": "Get feeding summary: total feed kg, recent daily feed, and FCR estimate.",
        "input_schema": {
            "type": "object",
            "properties": {"cycle_id": {"type": "string"}},
            "required": ["cycle_id"],
        },
    },
    {
        "name": "get_economics",
        "description": "Get economic data: total cost IDR, cost breakdown by category, and optimal harvest DOC from forecast.",
        "input_schema": {
            "type": "object",
            "properties": {"cycle_id": {"type": "string"}},
            "required": ["cycle_id"],
        },
    },
]

_INSIGHT_TOOL_REGISTRY = {
    "get_growth_metrics": _tool_get_growth_metrics,
    "get_water_quality": _tool_get_water_quality,
    "get_feeding_summary": _tool_get_feeding_summary,
    "get_economics": _tool_get_economics,
}


def _run_insight_tool(tool_name: str, tool_input: dict) -> str:
    fn = _INSIGHT_TOOL_REGISTRY.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return json.dumps(fn(**tool_input), default=str)
    except Exception as exc:
        logger.exception("Insight tool %s failed: %s", tool_name, exc)
        return json.dumps({"error": str(exc)})


_JSON_STRUCTURE = """{
  "summary": "2-3 sentence executive summary",
  "performance_score": <integer 0-100>,
  "metrics": [{"name":"...","current_value":...,"target_value":...,"unit":"...","status":"good|warning|critical","trend":"improving|stable|declining","insight":"..."}],
  "anomalies": [{"type":"water_quality|growth|feeding|economics","severity":"low|medium|high","description":"...","first_detected_doc":...,"recommendation":"..."}],
  "recommendations": [{"priority":"urgent|soon|monitor","action":"...","reason":"...","expected_impact":"..."}],
  "forecast_outlook": "1-2 sentence outlook"
}"""


class InsightService:

    @staticmethod
    def generate_insight(cycle_id: str, insight_type: str) -> tuple:
        """Generate a structured insight for a cycle. Caches result."""
        if insight_type not in VALID_TYPES:
            return 400, DataErrorSchema(
                code=400,
                message=f"Invalid insight type. Valid types: {', '.join(VALID_TYPES)}"
            )

        try:
            client = _get_client()
        except RuntimeError as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

        try:
            context = _build_cycle_context(cycle_id)
            current_doc = context.get("current_doc", 0)

            # Check cache: if generated at same DOC, return cached
            cached = CycleInsightCache.objects(
                cycle_id=cycle_id,
                insight_type=insight_type,
                doc_at_generation=current_doc,
            ).first()
            if cached:
                return 200, DataSuccessSchema(
                    code=200,
                    message="OK (cached)",
                    payload={"insight": cached.insight_data, "cached": True}
                )

            prompt = _build_prompt(insight_type, context)

            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = message.content[0].text.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            insight_data = json.loads(raw)
            insight_data["generated_at"] = datetime.utcnow().isoformat()
            insight_data["insight_type"] = insight_type
            insight_data["doc_at_generation"] = current_doc

            # Cache
            existing_cache = CycleInsightCache.objects(
                cycle_id=cycle_id, insight_type=insight_type
            ).first()
            if existing_cache:
                existing_cache.doc_at_generation = current_doc
                existing_cache.insight_data = insight_data
                existing_cache.generated_at = datetime.utcnow()
                existing_cache.model_used = "claude-sonnet-4-6"
                existing_cache.save()
            else:
                CycleInsightCache(
                    cycle_id=cycle_id,
                    insight_type=insight_type,
                    doc_at_generation=current_doc,
                    insight_data=insight_data,
                    model_used="claude-sonnet-4-6",
                ).save()

            return 200, DataSuccessSchema(
                code=200,
                message="OK",
                payload={"insight": insight_data, "cached": False}
            )

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Claude response as JSON: %s", exc)
            return 400, DataErrorSchema(code=400, message="Failed to parse AI response")
        except Exception as exc:
            logger.exception("Insight generation error for cycle %s: %s", cycle_id, exc)
            return 400, DataErrorSchema(code=400, message=str(exc))

    @staticmethod
    def get_cached_insight(cycle_id: str, insight_type: str) -> tuple:
        """Return cached insight without regenerating."""
        cached = CycleInsightCache.objects(
            cycle_id=cycle_id, insight_type=insight_type
        ).first()
        if not cached:
            return 400, DataErrorSchema(code=400, message="No cached insight found. Generate one first.")
        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={"insight": cached.insight_data, "cached": True}
        )

    @staticmethod
    def stream_insight(cycle_id: str, insight_type: str):
        """
        Generator that yields SSE-formatted chunks using Anthropic streaming.
        Uses tool-calling to let Claude fetch exactly what it needs.

        Agentic loop (max 3 rounds) with non-streaming tool-call resolution,
        then streams the final text response.
        """
        try:
            client = _get_client()
        except RuntimeError as exc:
            yield f'data: {json.dumps({"type": "error", "message": str(exc)})}\n\n'
            return

        type_instructions = {
            "performance": "Analyze overall cycle performance: growth rate, survival, FCR trend, and whether the cycle is on track.",
            "water_quality": "Analyze water quality trends: DO, temperature, NH3, pH, salinity. Identify any stress periods and their impact on growth.",
            "feeding": "Analyze feeding efficiency: feed given vs recommended, leftover trends, FCR trajectory, and cost of feeding.",
            "harvest": "Analyze harvest readiness: current ABW vs target, optimal harvest window, revenue projection.",
            "economics": "Analyze economics: cost breakdown, cost per kg trend, revenue forecast, profit projection.",
            "weekly": "Generate a concise weekly summary covering all key metrics, notable events, and recommendations for next week.",
        }
        instruction = type_instructions.get(insight_type, type_instructions["performance"])

        system_prompt = (
            f"You are an expert shrimp aquaculture analyst for Teramina. "
            f"You have tools to retrieve cycle data. Use them to gather the specific data you "
            f"need for this analysis, then generate a structured JSON insight.\n\n"
            f"Insight type requested: {insight_type}\n"
            f"Cycle ID: {cycle_id}\n"
            f"Instruction: {instruction}\n\n"
            f"IMPORTANT: After gathering data with tools, respond with ONLY valid JSON matching "
            f"this structure:\n{_JSON_STRUCTURE}\n\n"
            f"Rules:\n"
            f"- Be specific with numbers from the data. Do not invent values not present in the data.\n"
            f"- If data is missing, set the value to null and note it in the insight field.\n"
            f"- performance_score: 0=catastrophic, 50=average, 80=good, 100=excellent\n"
            f"- Only include anomalies that are genuinely present in the data\n"
            f"- Limit to 3 most important recommendations\n"
            f"- Respond in English unless the cycle name suggests Indonesian (then use Indonesian)"
        )

        messages = [
            {"role": "user", "content": f"Generate a {insight_type} insight for cycle {cycle_id}."}
        ]

        try:
            # Agentic loop: up to 3 rounds of tool calls (non-streaming)
            for _ in range(3):
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2048,
                    system=system_prompt,
                    tools=_INSIGHT_TOOL_DEFINITIONS,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    # No more tool calls needed — stream the final response
                    # Re-run as a streaming call with the same resolved messages
                    accumulated = ""
                    with client.messages.stream(
                        model="claude-sonnet-4-6",
                        max_tokens=2048,
                        system=system_prompt,
                        messages=messages,
                    ) as stream:
                        for chunk in stream.text_stream:
                            accumulated += chunk
                            yield f'data: {json.dumps({"type": "chunk", "text": chunk})}\n\n'

                    # Attempt to cache the accumulated result
                    try:
                        raw = accumulated.strip()
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.startswith("json"):
                                raw = raw[4:]
                        raw = raw.strip()
                        insight_data = json.loads(raw)
                        insight_data["generated_at"] = datetime.utcnow().isoformat()
                        insight_data["insight_type"] = insight_type

                        # Determine current DOC for cache key
                        cd = CycleData.objects(cycle_id=cycle_id).first()
                        current_doc = 0
                        if cd and cd.result_data:
                            docs = [r.get("doc") for r in cd.result_data if r.get("doc")]
                            current_doc = max(docs) if docs else 0
                        insight_data["doc_at_generation"] = current_doc

                        existing_cache = CycleInsightCache.objects(
                            cycle_id=cycle_id, insight_type=insight_type
                        ).first()
                        if existing_cache:
                            existing_cache.doc_at_generation = current_doc
                            existing_cache.insight_data = insight_data
                            existing_cache.generated_at = datetime.utcnow()
                            existing_cache.model_used = "claude-sonnet-4-6"
                            existing_cache.save()
                        else:
                            CycleInsightCache(
                                cycle_id=cycle_id,
                                insight_type=insight_type,
                                doc_at_generation=current_doc,
                                insight_data=insight_data,
                                model_used="claude-sonnet-4-6",
                            ).save()
                    except Exception as cache_exc:
                        logger.warning("stream_insight: cache write failed: %s", cache_exc)

                    yield 'data: {"type": "done"}\n\n'
                    return

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            yield f'data: {json.dumps({"type": "tool_call", "tool": block.name})}\n\n'
                            result_content = _run_insight_tool(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_content,
                            })

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # Unexpected stop reason — treat whatever text is there as final
                    accumulated = ""
                    for block in response.content:
                        if hasattr(block, "text"):
                            accumulated += block.text
                            yield f'data: {json.dumps({"type": "chunk", "text": block.text})}\n\n'
                    yield 'data: {"type": "done"}\n\n'
                    return

            # Exhausted max rounds without end_turn — stream whatever we can get now
            accumulated = ""
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
            ) as stream:
                for chunk in stream.text_stream:
                    accumulated += chunk
                    yield f'data: {json.dumps({"type": "chunk", "text": chunk})}\n\n'
            yield 'data: {"type": "done"}\n\n'

        except Exception as exc:
            logger.exception("stream_insight error for cycle %s: %s", cycle_id, exc)
            yield f'data: {json.dumps({"type": "error", "message": str(exc)})}\n\n'

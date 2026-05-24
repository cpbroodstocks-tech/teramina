# pylint: disable=broad-except
import os
import anthropic


def build_pl_narrative(report: dict) -> str:
    """Generate a 2-3 paragraph plain-text narrative for a P&L report using Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(api_key=api_key)

    kpi = report.get("kpi", {})
    net_pos = report.get("net_profit_idr", 0) >= 0
    gross_margin = report.get("gross_margin_pct", 0)
    net_margin = report.get("net_margin_pct", 0)

    prompt = f"""You are a financial analyst writing a narrative summary for a shrimp farming P&L report.
Write exactly 2-3 short paragraphs in English. Be direct, use the numbers below, and avoid generic filler.

Cycle: {report.get("cycle_name")} | Pond: {report.get("pond_name")}
Period: {report.get("doc_range")} | Active cycle: {report.get("is_active", False)}

Revenue: Rp {report.get("total_revenue_idr", 0):,}
COGS: Rp {report.get("total_cogs_idr", 0):,} | Gross profit: Rp {report.get("gross_profit_idr", 0):,} ({gross_margin}%)
OpEx: Rp {report.get("total_opex_idr", 0):,} | Net profit: Rp {report.get("net_profit_idr", 0):,} ({net_margin}%)
Total harvest: {kpi.get("total_harvest_kg", 0)} kg | FCR: {kpi.get("fcr", "—")} | SR: {kpi.get("survival_rate_pct", "—")}%
Cost/kg: Rp {kpi.get("cost_per_kg_idr", 0):,} | Revenue/kg: Rp {kpi.get("revenue_per_kg_idr", 0):,}
Profitable: {"Yes" if net_pos else "No"}

Paragraph 1: Summarize overall financial result and whether the cycle was profitable.
Paragraph 2: Discuss the main cost drivers and any standout KPIs (FCR, SR, cost/kg).
Paragraph 3: If active cycle, note projected figures. If complete, give a brief outlook or lesson.
Return plain text only — no markdown, no bullet points, no headers."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()

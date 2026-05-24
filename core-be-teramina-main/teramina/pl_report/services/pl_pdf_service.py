"""Build a P&L PDF using fpdf 1.7.2 (latin-1 safe)."""
from fpdf import FPDF


def _idr(n):
    if n is None:
        return "-"
    return f"Rp {int(n):,}"


def _pct(n):
    return f"{n}%" if n is not None else "-"


class _PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, "TERAMINA - Profit & Loss Statement", ln=True, align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 8)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")

    def section(self, title):
        self.set_font("Arial", "B", 11)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, title, ln=True, fill=True)
        self.set_font("Arial", size=10)

    def row(self, label, value, bold=False):
        if bold:
            self.set_font("Arial", "B", 10)
        else:
            self.set_font("Arial", size=10)
        self.cell(130, 7, f"  {label}", border="B")
        self.cell(50, 7, value, border="B", align="R", ln=True)

    def kpi_row(self, label, value):
        self.set_font("Arial", size=10)
        self.cell(100, 7, f"  {label}", border="B")
        self.cell(80, 7, str(value), border="B", align="R", ln=True)


def build_pl_pdf(report: dict) -> bytes:
    pdf = _PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header metadata
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, f"{report['cycle_name']} | {report['pond_name']}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 6, f"{report['doc_range']}  |  Start: {report.get('start_date') or '-'}  |  Currency: {report['currency']}", ln=True)
    status = "Active Cycle (projected figures included)" if report["is_active"] else "Completed Cycle"
    pdf.cell(0, 6, status, ln=True)
    pdf.cell(0, 6, f"Generated: {report['generated_at'][:19]}", ln=True)
    pdf.ln(4)

    # Revenue
    pdf.section("REVENUE")
    for evt in report["harvest_events"]:
        h_label = "Final" if evt["harvest_type"] == "final" else f"Partial {evt['harvest_no']}"
        label = f"{h_label} Harvest - DOC {evt['doc']} ({evt['biomass_kg']} kg)"
        pdf.row(label, _idr(evt["revenue_idr"]))
    if report.get("projected_remaining_idr") is not None:
        pdf.row("Remaining in pond (projected)", _idr(report["projected_remaining_idr"]))
    pdf.row("Total Revenue", _idr(report["total_revenue_idr"]), bold=True)
    pdf.ln(3)

    # COGS
    pdf.section("COST OF PRODUCTION (COGS)")
    if report["cost_seed_idr"]:
        pdf.row("Seed / Fry", _idr(report["cost_seed_idr"]))
    pdf.row("Feed", _idr(report["cost_feed_idr"]))
    pdf.row("Harvest Operations", _idr(report["cost_harvest_idr"]))
    pdf.row("Total COGS", _idr(report["total_cogs_idr"]), bold=True)
    pdf.row(f"Gross Profit  ({_pct(report['gross_margin_pct'])})", _idr(report["gross_profit_idr"]), bold=True)
    pdf.ln(3)

    # OpEx
    pdf.section("OPERATING EXPENSES")
    pdf.row("Labor", _idr(report["cost_labor_idr"]))
    pdf.row("Energy", _idr(report["cost_energy_idr"]))
    pdf.row("Probiotics & Treatment", _idr(report["cost_probiotics_idr"]))
    pdf.row("Bonus", _idr(report["cost_bonus_idr"]))
    pdf.row("Other", _idr(report["cost_other_idr"]))
    pdf.row("Total Operating Expenses", _idr(report["total_opex_idr"]), bold=True)
    pdf.ln(3)

    # Net
    pdf.section("NET RESULT")
    pdf.row("Total Cost", _idr(report["total_cost_idr"]), bold=True)
    pdf.row(f"Net Profit  ({_pct(report['net_margin_pct'])})", _idr(report["net_profit_idr"]), bold=True)
    pdf.ln(3)

    # KPIs
    pdf.section("KEY PERFORMANCE INDICATORS")
    kpi = report["kpi"]
    pdf.kpi_row("Cycle Duration", f"{kpi['doc']} days")
    pdf.kpi_row("Total Harvest", f"{kpi['total_harvest_kg']} kg")
    pdf.kpi_row("Final ABW", f"{kpi['final_abw_g']} g")
    pdf.kpi_row("Survival Rate", f"{kpi['survival_rate_pct']}%")
    pdf.kpi_row("FCR", kpi["fcr"])
    pdf.kpi_row("Cost / kg", _idr(kpi["cost_per_kg_idr"]))
    pdf.kpi_row("Revenue / kg", _idr(kpi["revenue_per_kg_idr"]))
    pdf.kpi_row("Break-even Price (per kg)", _idr(kpi["break_even_price_idr"]))

    return pdf.output(dest="S").encode("latin-1")

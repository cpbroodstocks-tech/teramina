# pylint: disable=broad-except
from datetime import date
from fpdf import FPDF


class _BankPDF(FPDF):
    def __init__(self, report: dict):
        super().__init__()
        self.report = report
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 8, "TERAMINA AQUACULTURE MANAGEMENT", ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "Jl. Tambak Raya No. 1, Jakarta, Indonesia", ln=True, align="C")
        self.cell(0, 5, "Tel: +62-21-0000000  |  info@teramina.id", ln=True, align="C")
        self.ln(3)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        ref = self.report.get("cycle_id", "")[:12].upper()
        self.cell(0, 5, f"Ref: TRM-{ref}  |  Page {self.page_no()}", align="C")

    def title_block(self):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, "PROFIT & LOSS STATEMENT", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, f"Farm: {self.report.get('pond_name', '')}  |  Cycle: {self.report.get('cycle_name', '')}", ln=True, align="C")
        self.cell(0, 6, f"Period: {self.report.get('doc_range', '')}  |  Start Date: {self.report.get('start_date', '')}", ln=True, align="C")
        self.cell(0, 6, f"Currency: {self.report.get('currency', 'IDR')}  |  Generated: {date.today().strftime('%d %B %Y')}", ln=True, align="C")
        self.ln(4)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(3)

    def ref_block(self):
        ref = self.report.get("cycle_id", "")[:12].upper()
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, f"Document Reference: TRM-PL-{ref}", ln=True)
        self.cell(0, 5, f"Prepared by: Teramina Platform (Automated Report)", ln=True)
        self.cell(0, 5, f"Date of Issue: {date.today().strftime('%d %B %Y')}", ln=True)
        self.ln(3)

    def section_header(self, title: str):
        self.set_fill_color(30, 60, 100)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, f"  {title}", ln=True, fill=True)
        self.set_text_color(0, 0, 0)

    def data_row(self, label: str, value: str, bold: bool = False, indent: int = 0):
        self.set_font("Helvetica", "B" if bold else "", 9)
        lw = 120 - indent
        self.set_x(20 + indent)
        self.cell(lw, 6, label)
        self.cell(0, 6, value, ln=True, align="R")

    def divider(self):
        self.set_draw_color(180, 180, 180)
        self.line(20, self.get_y(), 190, self.get_y())
        self.set_draw_color(0, 0, 0)
        self.ln(1)


def _idr(n) -> str:
    if n is None:
        return "—"
    return f"Rp {int(n):,}".replace(",", ".")


def build_bank_pdf(report: dict) -> bytes:
    pdf = _BankPDF(report)
    pdf.add_page()
    pdf.title_block()
    pdf.ref_block()

    # Revenue
    pdf.section_header("I. REVENUE")
    for evt in report.get("harvest_events", []):
        label = (
            f"  Final Harvest (DOC {evt['doc']})"
            if evt["harvest_no"] == len(report["harvest_events"])
            else f"  Partial Harvest {evt['harvest_no']} (DOC {evt['doc']})"
        )
        pdf.data_row(label, _idr(evt.get("revenue_idr")), indent=4)
    if report.get("projected_remaining_idr") is not None:
        pdf.data_row("  Remaining in pond (projected)", _idr(report["projected_remaining_idr"]), indent=4)
    pdf.divider()
    pdf.data_row("Total Revenue", _idr(report.get("total_revenue_idr")), bold=True)
    pdf.ln(2)

    # COGS
    pdf.section_header("II. COST OF PRODUCTION (COGS)")
    if report.get("cost_seed_idr", 0):
        pdf.data_row("  Seed / Fry", _idr(report["cost_seed_idr"]), indent=4)
    pdf.data_row("  Feed", _idr(report.get("cost_feed_idr")), indent=4)
    pdf.data_row("  Harvest Operations", _idr(report.get("cost_harvest_idr")), indent=4)
    pdf.divider()
    pdf.data_row("Total COGS", _idr(report.get("total_cogs_idr")), bold=True)
    pdf.data_row(
        f"Gross Profit ({report.get('gross_margin_pct', 0)}%)",
        _idr(report.get("gross_profit_idr")),
        bold=True,
    )
    pdf.ln(2)

    # OpEx
    pdf.section_header("III. OPERATING EXPENSES (OPEX)")
    pdf.data_row("  Labor", _idr(report.get("cost_labor_idr")), indent=4)
    pdf.data_row("  Energy", _idr(report.get("cost_energy_idr")), indent=4)
    pdf.data_row("  Probiotics & Treatment", _idr(report.get("cost_probiotics_idr")), indent=4)
    pdf.data_row("  Bonus", _idr(report.get("cost_bonus_idr")), indent=4)
    pdf.data_row("  Other", _idr(report.get("cost_other_idr")), indent=4)
    pdf.divider()
    pdf.data_row("Total Operating Expenses", _idr(report.get("total_opex_idr")), bold=True)
    pdf.ln(2)

    # Net result
    pdf.section_header("IV. NET RESULT")
    pdf.data_row("Total Cost (COGS + OPEX)", _idr(report.get("total_cost_idr")), bold=True)
    pdf.data_row(
        f"Net Profit / (Loss) ({report.get('net_margin_pct', 0)}%)",
        _idr(report.get("net_profit_idr")),
        bold=True,
    )
    pdf.ln(4)

    # KPIs
    pdf.section_header("V. KEY PERFORMANCE INDICATORS")
    kpi = report.get("kpi", {})
    rows = [
        ("Cycle Duration (days)", str(kpi.get("doc", "—"))),
        ("Total Harvest Volume", f"{kpi.get('total_harvest_kg', '—')} kg"),
        ("Final Average Body Weight", f"{kpi.get('final_abw_g', '—')} g"),
        ("Survival Rate", f"{kpi.get('survival_rate_pct', '—')}%"),
        ("Feed Conversion Ratio (FCR)", str(kpi.get("fcr", "—"))),
        ("Cost per kg", _idr(kpi.get("cost_per_kg_idr"))),
        ("Revenue per kg", _idr(kpi.get("revenue_per_kg_idr"))),
        ("Break-even Price per kg", _idr(kpi.get("break_even_price_idr"))),
    ]
    for label, val in rows:
        pdf.data_row(f"  {label}", val, indent=4)
    pdf.ln(6)

    # Signatory block
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "This report is generated by the Teramina platform based on recorded farm data.", ln=True)
    if report.get("is_active"):
        pdf.cell(0, 5, "* Projected figures are estimates for active cycles and may change.", ln=True)
    pdf.ln(8)

    col = 57
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(col, 5, "Prepared by,")
    pdf.cell(col, 5, "Reviewed by,")
    pdf.cell(col, 5, "Approved by,")
    pdf.ln(16)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(col, 5, "( _________________ )")
    pdf.cell(col, 5, "( _________________ )")
    pdf.cell(col, 5, "( _________________ )")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(col, 5, "Farm Manager")
    pdf.cell(col, 5, "Finance Officer")
    pdf.cell(col, 5, "Director")

    return pdf.output(dest="S").encode("latin-1")

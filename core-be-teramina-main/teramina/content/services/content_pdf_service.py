"""Build content-library PDFs using fpdf 1.7.2."""
from datetime import datetime
import re

from fpdf import FPDF


def _safe_text(value):
    return (value or "").encode("latin-1", "replace").decode("latin-1")


def _clean_markdown(line):
    line = re.sub(r"`([^`]*)`", r"\1", line)
    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
    line = re.sub(r"\*([^*]+)\*", r"\1", line)
    return _safe_text(line.strip())


class _ContentPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, "TERAMINA - Knowledge Library", ln=True, align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 8)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")


def _write_line(pdf, line):
    stripped = line.strip()
    if not stripped:
        pdf.ln(3)
        return

    if stripped.startswith("# "):
        pdf.set_font("Arial", "B", 15)
        pdf.multi_cell(0, 8, _clean_markdown(stripped[2:]))
        pdf.ln(2)
        return

    if stripped.startswith("## "):
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.multi_cell(0, 8, _clean_markdown(stripped[3:]), fill=True)
        pdf.ln(1)
        return

    if stripped.startswith("### "):
        pdf.set_font("Arial", "B", 11)
        pdf.multi_cell(0, 7, _clean_markdown(stripped[4:]))
        return

    if stripped.startswith(("- ", "* ")):
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, f"- {_clean_markdown(stripped[2:])}")
        return

    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, _clean_markdown(stripped))


def build_content_pdf(item) -> bytes:
    pdf = _ContentPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 9, _safe_text(item.title))
    pdf.set_font("Arial", size=9)
    pdf.cell(0, 6, _safe_text(f"{item.category} | {item.content_type} | v{item.version}"), ln=True)
    pdf.cell(0, 6, _safe_text(f"Generated: {datetime.now().isoformat()[:19]}"), ln=True)
    if item.summary:
        pdf.ln(3)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 6, _safe_text(item.summary))
    pdf.ln(4)

    body = item.body_markdown or "No markdown body is available for this document."
    for line in body.splitlines():
        _write_line(pdf, line)

    return pdf.output(dest="S").encode("latin-1")

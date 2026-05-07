"""report generator service"""

from fpdf import FPDF


class PDF(FPDF):
    """Customize FPDF Function"""

    def header(self):
        """custom header"""
        # Select Arial bold 15
        self.set_font("Arial", "B", 15)
        self.image("header-2.png", x=0, y=0, w=220)
        # Line break
        self.ln(60)

    def footer(self):
        """custom footer"""
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font("Arial", "I", 8)
        # Page number
        self.cell(0, 10, "Page " + str(self.page_no()), 0, 0, "C")

    def h1(self, title):
        """custom h1"""
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(6)
        self.set_font("Arial", size=12)

    def h2(self, title):
        """custom h2"""
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(5)
        self.set_font("Arial", size=12)

    def h3(self, title):
        """custom h3"""
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, 0, 1, "L")
        self.set_font("Arial", size=12)

    def add_table(self, data, col_widths):
        """add table"""
        for row in data:
            for item, width in zip(row, col_widths):
                self.cell(width, 10, str(item), border=1)
            self.ln()


def parse_data(pdf: PDF, data: dict, layer: int = 1):
    """parsing data from dict data"""
    if data["title"]:
        if layer == 1:
            pdf.h1(data["title"])
        elif layer == 2:
            pdf.h2(data["title"])
        else:
            pdf.h3(data["title"])

    if data["interpretation"]:
        pdf.multi_cell(0, 5, txt=data["interpretation"])

    if data["type"] == "image":
        pdf.image(
            data["url"], x=data["config"]["location_x"], w=data["config"]["width"]
        )

    if data["type"] == "table":
        pdf.add_table(data["table_data"], data["table_column_widths"])
        pdf.ln(2)


def generate_pdf_report_with_data(report_contents: dict):
    """generate pdf report with data"""
    # Create instance of PDF class
    pdf = PDF()
    pdf.add_page()

    report_data = report_contents["content"]

    for data in report_data:
        parse_data(pdf, data, 1)
        if data["content"]:
            for sub_data in data["content"]:
                parse_data(pdf, sub_data, 2)
                if sub_data["content"]:
                    for sub_sub_data in sub_data["content"]:
                        parse_data(pdf, sub_sub_data, 3)

    # Save the pdf with name .pdf
    # pdf.output(output_file)
    pdf_output = pdf.output(dest="S").encode("latin1")
    return pdf_output

from myapp.utils.logger_config import get_logger
from typing import Any

log = get_logger(__name__)
from fpdf import FPDF
from pathlib import Path

# Defaults
DEFAULT_LOGO_PATH = Path("static/signatures/logo.png")
DEFAULT_FONT = "Helvetica"
TITLE_FONT_SIZE = 14
NORMAL_FONT_SIZE = 11
HEADER_MARGIN = 15
LINE_HEIGHT = 8
LABEL_WIDTH = 40


class JobReportPDF(FPDF):
    """
    PDF subclass tailored for AutoClose job reports.
    Adds a custom header (with optional logo), footer, and job-detail blocks.
    """

    def __init__(self, logo_path: Path = DEFAULT_LOGO_PATH):
        super().__init__()
        self.logo_path = logo_path
        self.set_auto_page_break(auto=True, margin=HEADER_MARGIN)
        self.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
        self.set_font('DejaVu', '', NORMAL_FONT_SIZE)
        self.failed_fields: set[str] = set()

    def header(self) -> None:
        """
        Draws the header on each page: embed logo if available, then title.
        """
        # Logo embedding
        if self.logo_path.is_file():
            try:
                self.image(str(self.logo_path), x=10, y=8, w=30)
            except Exception as e:
                log.warning("Logo embed failed (%s): %s", self.logo_path, e)
        # Title text
        self.set_font('DejaVu', 'B', TITLE_FONT_SIZE)
        self.cell(0, 10, "AutoClose - Job Report", ln=True, align="C")
        self.ln(5)

    def footer(self) -> None:
        """
        Draws the footer on each page with page numbers.
        """
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        page_str = f"Page {self.page_no()}/{{nb}}"
        self.cell(0, 10, page_str, align="C")

    def add_job_block(self, job: dict) -> None:
        """
        Adds a section for a single job's details.

        :param job: Mapping of field identifiers to their values.
        """
        for field, value in job.items():
            label = field.replace("_", " ").capitalize()
            # Label in bold
            self.set_font('DejaVu', 'B', NORMAL_FONT_SIZE)
            self.cell(LABEL_WIDTH, LINE_HEIGHT, f"{label}:", ln=0)
            # Value text
            self.set_font('DejaVu', '', NORMAL_FONT_SIZE)
            text = str(value).strip() if value else "-"
            if not text or len(text) > 1000:
                text = "[value too long]"
            try:
                self.multi_cell(0, LINE_HEIGHT, text)
            except Exception as e:
                if field not in self.failed_fields:
                    log.warning("Failed to render cell for field %s: %s", field, e)
                    self.failed_fields.add(field)
                self.cell(0, LINE_HEIGHT, "[render error]", ln=True)
        self.ln(5)

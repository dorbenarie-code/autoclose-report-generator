from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from pathlib import Path
from datetime import datetime
from typing import Union

from myapp.utils.file_validator import load_and_clean_data
from myapp.services.report_generation.job_pdf import JobReportPDF

# Defaults and constants
OUTPUT_DIR = Path("output/reports_exported")
LOGO_PATH = Path("static/signatures/logo.png")
CSV_DEFAULT_PATH = Path("output/merged_jobs.csv")

FIELD_MAP = [
    ("name", "Client Name"),
    ("phone", "Phone"),
    ("address", "Address"),
    ("timestamp", "Date"),
    ("technician", "Technician"),
    ("service_type", "Service Type"),
    ("car", "Car"),
    ("notes", "Notes"),
    ("payment_type", "Payment"),
    ("total", "Total"),
    ("parts", "Parts"),
    ("code", "Job Code"),
    ("job_id", "Job ID"),
]


def generate_detailed_report(csv_path: Union[str, Path] = CSV_DEFAULT_PATH) -> Path:
    """
    1. Load and clean CSV/Excel data
    2. Early exit on empty DataFrame
    3. Build PDF: logo, title, timestamped filename
    4. Iterate rows safely, add each job block
    5. Write PDF to disk and return its Path
    """
    csv_file = Path(csv_path)
    if not csv_file.is_file():
        log.error("Report source not found: %s", csv_file)
        raise FileNotFoundError(f"No such file: {csv_file}")

    df = load_and_clean_data(str(csv_file))
    if df.empty:
        log.warning("No data to report in: %s", csv_file)
        raise ValueError("Uploaded file contains no valid data rows.")

    pdf = _initialize_pdf()
    _add_logo_if_available(pdf)
    _add_title(pdf)

    for idx, row in df.iterrows():
        # build a dict mapping field keys → safe string values
        job = {key: (row.get(key) or "") for key, _ in FIELD_MAP}
        pdf.add_job_block(job)

    output_path = _export_pdf(pdf)
    log.info("Report successfully generated at %s", output_path)
    return output_path


def _initialize_pdf() -> JobReportPDF:
    """Create PDF object and open first page."""
    pdf = JobReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    return pdf


def _add_logo_if_available(pdf: JobReportPDF) -> None:
    """Place logo at top-left if the file exists."""
    if LOGO_PATH.is_file():
        try:
            pdf.image(str(LOGO_PATH), x=10, y=8, w=30)
        except Exception as e:
            log.warning("Failed to embed logo (%s): %s", LOGO_PATH, e)


def _add_title(pdf: JobReportPDF) -> None:
    """Add centered title and generation timestamp."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', 'B', 16)
    pdf.cell(0, 15, "Detailed Job Report", ln=True, align="C")
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(0, 10, f"Generated: {now_str}", ln=True, align="C")
    pdf.ln(10)


def _export_pdf(pdf: JobReportPDF) -> Path:
    """
    Ensure output directory exists, write PDF file with timestamped name,
    and return the full Path.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Detailed_Report_{ts}.pdf"
    out_path = OUTPUT_DIR / filename

    try:
        pdf.output(str(out_path))
    except Exception as e:
        log.error("Failed to write PDF to %s: %s", out_path, e)
        raise

    return out_path


if __name__ == "__main__":
    # Example: Generate a report and check PDF validity
    output_path = generate_detailed_report()
    log.info(f"Generated PDF: {output_path}")
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(output_path))
        log.info(f"PDF opened successfully. Number of pages: {len(reader.pages)}")
    except Exception as e:
        log.info(f"PDF validation failed: {e}")

import os
import pandas as pd
from fpdf import FPDF
from datetime import datetime

OUTPUT_DIR = "output/reports_exported"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FIELD_MAP = [
    ("name", "Name"),
    ("phone", "Phone"),
    ("job_id", "Job ID"),
    ("address", "Address"),
    ("service_type", "Service Type"),
    ("car", "Car"),
    ("notes", "Notes"),
    ("technician", "Technician"),
    ("payment_type", "Payment"),
    ("total", "Total"),
    ("parts", "Parts"),
    ("code", "Code"),
    ("timestamp", "Timestamp"),
]


def load_jobs(csv_path):
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, sep=",", quotechar='"')
    df = df[df.apply(lambda row: any(row.values), axis=1)]
    df = df[~df.iloc[:, 0].str.lower().str.startswith(("total", "totals"))]
    return df


class JobReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)
        self.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
        self.set_font('DejaVu', '', 12)
        self.jobs_in_page = 0

    def header(self):
        self.set_font('DejaVu', 'B', 14)
        self.cell(
            0,
            10,
            "PRO ON CALL SERVICES INC - Detailed Jobs Report",
            new_y="NEXT",
            align="C",
        )
        self.set_font('DejaVu', '', 10)
        self.cell(
            0,
            8,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            new_y="NEXT",
            align="C",
        )
        self.ln(2)

    def add_job_block(self, job_dict):
        if self.jobs_in_page >= 5:
            self.add_page()
            self.jobs_in_page = 0
        elif self.jobs_in_page > 0:
            self.ln(8)
        self.set_font('DejaVu', 'B', 12)
        name = job_dict.get("name", "").strip()
        if name:
            self.cell(0, 8, f"Name: {name}", new_y="NEXT")
        self.set_font('DejaVu', '', 11)
        phone = job_dict.get("phone", "").strip()
        job_id = job_dict.get("job_id", "").strip()
        if phone or job_id:
            self.cell(0, 7, f"({phone} {job_id})".strip(), new_y="NEXT")
        address = job_dict.get("address", "").strip()
        if address:
            self.cell(0, 7, address, new_y="NEXT")
        service_type = job_dict.get("service_type", "").strip()
        car = job_dict.get("car", "").strip()
        if service_type:
            self.cell(0, 7, service_type, new_y="NEXT")
        if car:
            self.cell(0, 7, car, new_y="NEXT")
        notes = job_dict.get("notes", "").strip()
        if notes:
            self.cell(0, 7, notes, new_y="NEXT")
        timestamp = job_dict.get("timestamp", "").strip()
        if timestamp:
            self.cell(0, 7, timestamp, new_y="NEXT")
        self.ln(2)
        self.set_font('DejaVu', '', 10)
        self.cell(0, 6, "PRO ON CALL SERVICES INC", new_y="NEXT")
        technician = job_dict.get("technician", "").strip()
        if technician:
            self.cell(0, 6, technician, new_y="NEXT")
        total = job_dict.get("total", "").strip()
        payment_type = job_dict.get("payment_type", "").strip()
        if total or payment_type:
            self.cell(0, 6, f"{total}$ {payment_type}".strip(), new_y="NEXT")
        parts = job_dict.get("parts", "").strip()
        if parts:
            self.cell(0, 6, f"{parts}$ parts", new_y="NEXT")
        code = job_dict.get("code", "").strip()
        if code:
            self.cell(0, 6, code, new_y="NEXT")
        self.jobs_in_page += 1


def generate_detailed_report(csv_path: str = "output/merged_jobs.csv") -> str:
    df = load_jobs(csv_path)
    pdf = JobReportPDF()
    pdf.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    pdf.add_page()
    for _, row in df.iterrows():
        job = {k: row.get(k, "") for k, _ in FIELD_MAP}
        pdf.add_job_block(job)
    now = datetime.now()
    filename = f"Detailed_Report_{now.strftime('%Y%m%d_%H%M')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(output_path)
    return output_path

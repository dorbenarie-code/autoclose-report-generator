import os
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from myapp.utils.logger_config import get_logger
from myapp.config_shortcuts import EXPORT_DIR

log = get_logger(__name__)

# Directory to store exported PDF reports
os.makedirs(EXPORT_DIR, exist_ok=True)


class PDFReportExporter:
    """
    A helper class to export a DataFrame to a PDF file,
    including a title, date/time, a Plotly histogram, and a basic data table.

    Attributes
    ----------
    df : pd.DataFrame
        The DataFrame to be exported (report data).
    title : str
        A custom title for the PDF report.
    filename : str
        The filename of the PDF. Automatically generated with timestamp.
    full_path : str
        The full path of the PDF file to be created in EXPORT_DIR.

    Methods
    -------
    generate_plot_image(image_path)
        Creates a Plotly histogram, saves it as a PNG image.
    export(filename: str = None) -> str
        Builds the PDF with header, date, image, and table. Returns the PDF filename.
    export_overview(kpi: dict, summary: dict, df: pd.DataFrame, output_path: Path)
        Exports an overview report with KPIs, technician performance, and raw data.
    """

    def __init__(
        self,
        df: Optional[pd.DataFrame] = None,
        title: Optional[str] = None,
        export_dir: Path = Path("output/client_reports"),
    ) -> None:
        self.df = df
        self.title = title
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)
        if title:
            self.filename = f"{title.replace(' ', '_')}.pdf"
            self.full_path = str(self.export_dir / self.filename)

    def generate_plot_image(self, image_path: str) -> None:
        """Generate a histogram plot image using Plotly."""
        fig = px.histogram(
            self.df,
            x="tech",
            title="Technician Job Distribution",
            labels={"tech": "Technician", "count": "Count of Reports"},
        )
        pio.write_image(fig, image_path, format="png", scale=2)

    def export(self, filename: Optional[str] = None) -> str:
        """
        Generate and save the PDF report.
        Returns the full path to the generated PDF file.
        """
        if filename:
            self.filename = filename
            self.full_path = str(self.export_dir / filename)

        # Initialize PDF (Portrait, millimeters, A4)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        # ► Unicode font support
        pdf.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 14)
        # Title (centered, bold)
        pdf.set_font('DejaVu', 'B', 16)
        pdf.cell(0, 10, text=self.title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        # Date (small text, default font)
        pdf.set_font('DejaVu', '', 10)
        pdf.cell(
            0,
            8,
            text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        # Generate the Plotly histogram image
        image_path = str(Path(self.full_path).with_suffix(".png"))
        self.generate_plot_image(image_path)

        # Insert the image into the PDF
        # w=180 to make it nicely wide on A4, respecting margins
        pdf.image(image_path, w=180)
        # Remove the PNG file after insertion
        os.remove(image_path)

        # Table heading
        pdf.ln(5)  # a bit of vertical spacing before the table
        pdf.set_font('DejaVu', 'B', 12)
        pdf.cell(
            0,
            8,
            text="Report Data (first 20 rows):",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        # Table content
        pdf.set_font('DejaVu', '', 9)
        if self.df is None:
            raise ValueError("Expected non-empty DataFrame")
        table_data = self.df.head(20).fillna("").astype(str).values.tolist()

        # For each row in the data, we create a multi_cell line
        # Or you can do your own formatting with fixed column widths
        for row in table_data:
            row_text = " | ".join(row)
            safe_text = str(row_text).strip() if row_text else "-"
            if not safe_text or len(safe_text) > 1000:
                safe_text = "[text too long]"
            try:
                pdf.multi_cell(0, 5, text=safe_text)
            except Exception as e:
                pdf.cell(
                    0, 5, text="[render error]", new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )

        # Save the final PDF
        pdf.output(self.full_path)

        # Log the file size after saving
        log.info(
            f"📁 PDF report saved: {self.full_path} | Size: {Path(self.full_path).stat().st_size} bytes"
        )

        return self.full_path

    def export_overview(
        self,
        kpi: dict[str, Any],
        summary: dict[str, Any],
        df: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """
        Exports an overview report with KPIs, technician performance, and raw data.

        Args:
            kpi: Dictionary containing KPI metrics
            summary: Dictionary containing summary data including technician performance
            df: Raw DataFrame with all data
            output_path: Path where to save the PDF
        """
        # Initialize PDF (Portrait, millimeters, A4)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        # ► Unicode font support
        pdf.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 14)
        # Title
        pdf.set_font('DejaVu', 'B', 16)
        pdf.cell(
            0,
            10,
            text="Overview Report",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="C",
        )
        # Date
        pdf.set_font('DejaVu', '', 10)
        pdf.cell(
            0,
            8,
            text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # KPI Section
        pdf.ln(5)
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(0, 8, text="KPI Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('DejaVu', '', 10)
        for key, value in kpi.items():
            if isinstance(value, (int, float)):
                text = f"{key}: {value:,.2f}"
            else:
                text = f"{key}: {value}"
            pdf.cell(0, 6, text=text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Technician Performance Section
        pdf.ln(5)
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(
            0, 8, text="Technician Performance", new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        if "by_tech" in summary:
            tech_df = summary["by_tech"]
            # Table header
            pdf.set_font('DejaVu', 'B', 10)
            headers = list(tech_df.columns)
            col_width = 190 / len(headers)  # 190mm is roughly A4 width minus margins
            for header in headers:
                pdf.cell(col_width, 6, text=str(header), border=1)
            pdf.ln()
            # Table content
            pdf.set_font('DejaVu', '', 9)
            for _, row in tech_df.iterrows():
                for value in row:
                    pdf.cell(col_width, 6, text=str(value), border=1)
                pdf.ln()
        # Raw Data Section (first 20 rows)
        pdf.ln(5)
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(
            0, 8, text="Raw Data (first 20 rows)", new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        pdf.set_font('DejaVu', '', 9)
        if df is None:
            raise ValueError("Expected non-empty DataFrame")
        table_data = df.head(20).fillna("").astype(str).values.tolist()
        for row in table_data:
            row_text = " | ".join(row)
            safe_text = str(row_text).strip() if row_text else "-"
            if not safe_text or len(safe_text) > 1000:
                safe_text = "[text too long]"
            try:
                pdf.multi_cell(0, 5, text=safe_text)
            except Exception as e:
                pdf.cell(
                    0, 5, text="[render error]", new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
        # Save the PDF
        pdf.output(str(output_path))
        log.info(
            f"📁 Overview PDF saved: {output_path} | Size: {output_path.stat().st_size} bytes"
        )


def standardize_columns(df: pd.DataFrame) -> None:
    return None

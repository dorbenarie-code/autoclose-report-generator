import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from flask import send_file, current_app
from myapp.services.pdf_export_service import PDFReportExporter
from tempfile import NamedTemporaryFile
from myapp.utils.logger_config import get_logger
from typing import Any
from myapp.config_shortcuts import EXPORT_DIR

log = get_logger(__name__)


def get_export_root() -> Path:
    return Path(current_app.config.get("EXPORT_DIR", "output/reports_exported"))


def _ensure_dir() -> None:
    get_export_root().mkdir(parents=True, exist_ok=True)


def _timestamped_name(prefix: str, ext: str) -> str:
    return f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}.{ext}"


def export_overview_csv(df: pd.DataFrame, kpi: dict, summary: dict) -> Any:
    log.debug("TYPECHECK: %s in export_overview_csv", type(df).__name__)
    _ensure_dir()
    filename = _timestamped_name("overview", "csv")
    filepath = get_export_root() / filename
    df.to_csv(filepath, index=False)
    log.info(f"✅ CSV exported to {filepath}")
    return send_file(
        filepath, as_attachment=True, download_name=filename, mimetype="text/csv"
    )


def export_overview_excel(df: pd.DataFrame, kpi: dict, summary: dict) -> Any:
    log.debug("TYPECHECK: %s in export_overview_excel", type(df).__name__)
    _ensure_dir()
    # Use NamedTemporaryFile to avoid partial writes
    with NamedTemporaryFile(
        prefix="overview_", suffix=".xlsx", dir=get_export_root(), delete=False
    ) as tmp:
        with pd.ExcelWriter(tmp.name, engine="openpyxl") as writer:
            pd.DataFrame([kpi]).to_excel(writer, sheet_name="KPIs", index=False)
            summary.get("by_tech", pd.DataFrame()).to_excel(
                writer, sheet_name="Technicians", index=False
            )
            df.to_excel(writer, sheet_name="Raw Data", index=False)
        filename = Path(tmp.name).name
    log.info(f"✅ Excel exported to {tmp.name}")
    return send_file(
        tmp.name,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def export_overview_pdf(df: pd.DataFrame, kpi: dict, summary: dict) -> Any:
    log.debug("TYPECHECK: %s in export_overview_pdf", type(df).__name__)
    _ensure_dir()
    filename = _timestamped_name("overview", "pdf")
    output_path = get_export_root() / filename
    exporter = PDFReportExporter()
    exporter.export_overview(kpi, summary, df, output_path)
    log.info(f"✅ PDF exported to {output_path}")
    return send_file(
        output_path,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )

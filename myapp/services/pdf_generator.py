from myapp.utils.logger_config import get_logger
from myapp.utils.manifest import add_report_to_manifest
from myapp.utils.report_validation import validate_report_integrity
from myapp.utils.chart_utils import save_income_chart
from myapp.utils.dataframe_utils import append_totals_row, format_currency_columns, enrich, format_report_columns, coerce_dates, enrich_financials
from pandas import DataFrame, Series
import logging

log = logging.getLogger(__name__)
import os
from datetime import datetime
from typing import List, Optional, Any
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from myapp.finance.insights.engine import InsightsEngine
from myapp.tasks.task_engine import create_action_item

# אם אין לך כבר:
# pip install fpdf
try:
    from fpdf import FPDF
except ImportError:
    raise ImportError("התקן את FPDF באמצעות pip install fpdf")


# הגדרות בסיסיות (אפשר להוציא לקובץ config)
OUTPUT_DIR = "output"
LOGO_DIR = os.path.join("static", "logos")
MAX_COLS_PORTRAIT = 8
LOGO_DEFAULT_WIDTH = 30  # מ"מ
PAGE_MARGIN = 10  # מ"מ שול
PAGE_BOTTOM_MARGIN = 15  # שול תחתון ברירת מחדל
LONG_COLUMN_FACTOR = 1.5  # כמה עמודות 'ארוכות' יקבלו יותר מקום
MAX_COLS_PER_TABLE = 15

MIN_PDF_SIZE_BYTES = 10_000  # 10 KB
MIN_DATA_ROWS = 1            # excluding totals row
MIN_TOTAL_SUM = 0.01         # strictly positive


class PDFReportError(Exception):
    """שגיאה ממוקדת לבעיות ביצירת PDF."""

    pass


def _find_logo_path(client_id: str) -> Optional[str]:
    """
    מחפש קובץ לוגו לפי client_id בכמה סיומות שכיחות.
    מחזיר את המסלול אם נמצא, אחרת None.
    """
    extensions = [".png", ".jpg", ".jpeg"]
    for ext in extensions:
        path = os.path.join(LOGO_DIR, f"{client_id}{ext}")
        if os.path.isfile(path):
            return path
    return None


def _add_logo(
    pdf: FPDF,
    client_id: str,
    width: int = LOGO_DEFAULT_WIDTH,
    x: int = PAGE_MARGIN,
    y: int = 8,
) -> None:
    """
    מוסיף לוגו ל-PDF, אם קיים, ומעדכן את מיקום הראשונית למעבר לטקסט.
    """
    logo_path = _find_logo_path(client_id)
    if logo_path:
        pdf.image(logo_path, x=x, y=y, w=width)
        pdf.set_xy(x + width + 5, y + 5)  # מרווח אחרי הלוגו
    else:
        pdf.set_xy(PAGE_MARGIN, 15)


def _calculate_col_widths(
    columns: list[str], total_width: float, max_cols: int
) -> list[float]:
    """
    מחשבת את רוחב כל עמודה בהתאם לאורך שם העמודה/תוכן.
    אם סה"כ הרוחב חורג מהעמוד, נעשה scale down.
    """
    base_width = total_width / max_cols
    col_widths = []
    for col in columns:
        # בדיקה גסה אם זה עמודה 'ארוכה'
        if len(col) > 12 or col.lower() in {"description", "remarks", "notes"}:
            col_widths.append(base_width * LONG_COLUMN_FACTOR)
        else:
            col_widths.append(base_width)

    total = sum(col_widths)
    if total > total_width:
        scale = total_width / total
        col_widths = [w * scale for w in col_widths]

    return col_widths


def _print_table_header(pdf: FPDF, columns: list[str], col_widths: list[float], font_name: str) -> None:
    """
    מדפיס כותרת טבלה (שורת ה-Header) בפונט מודגש, עם גבולות.
    """
    pdf.set_font(font_name, "B", 12)
    for col, width in zip(columns, col_widths):
        pdf.cell(width, 10, txt=col, border=1, align="C")
    pdf.ln()
    pdf.set_font(font_name, size=10)


def _print_single_row(
    pdf: FPDF,
    row_data: pd.Series,
    columns: list[str],
    col_widths: list[float],
    line_height: float,
    font_name: str
) -> float:
    """
    מדפיסה שורה בודדת באמצעות multi_cell לכל תא, מחזירה את הגובה של השורה (למקרה שיש עטיפה).
    """
    y_start = pdf.get_y()
    max_cell_height = 0

    for col, width in zip(columns, col_widths):
        text = str(row_data[col]) if pd.notna(row_data[col]) else ""
        x = pdf.get_x()
        y = pdf.get_y()

        pdf.multi_cell(width, line_height, text, border=1)
        cell_height = pdf.get_y() - y
        if cell_height > max_cell_height:
            max_cell_height = cell_height

        pdf.set_xy(x + width, y_start)

    # מעדכנים את y לסוף השורה
    pdf.set_y(y_start + max_cell_height)
    return max_cell_height


def _print_table_rows(
    pdf: FPDF,
    df: pd.DataFrame,
    columns: list[str],
    col_widths: list[float],
    font_name: str,
    start_index: int = 0
) -> Any:
    """
    מדפיסה את השורות בטבלה, כולל טיפול במעבר עמוד. בכל מעבר עמוד מחזירה אינדקס
    כדי שניתן יהיה להדפיס מחדש את כותרות הטבלה ולהמשיך בשורות.
    """
    line_height = 8
    page_height_limit = pdf.h - PAGE_BOTTOM_MARGIN  # גבול תחתון

    for i in range(start_index, len(df)):
        # בדיקה אם צריך עמוד חדש
        if pdf.get_y() + line_height * 2 > page_height_limit:
            pdf.add_page()
            yield i
            return

        row_data = df.iloc[i]
        _print_single_row(pdf, row_data, columns, col_widths, line_height, font_name)

    yield None


def _print_full_table(pdf: FPDF, df: pd.DataFrame, col_widths: list[float], font_name: str) -> None:
    """
    מדפיסה את הטבלה במלואה, כולל כותרות חוזרות בכל מעבר עמוד.
    """
    columns = list(df.columns)
    start = 0
    while True:
        row_gen = _print_table_rows(pdf, df, columns, col_widths, font_name, start_index=start)
        next_start = next(row_gen, None)
        if next_start is None:
            break
        # אם יש עוד שורות, נחזור להדפיס כותרות בעמוד החדש ונמשיך
        _print_table_header(pdf, columns, col_widths, font_name)
        start = next_start


def _split_columns_if_needed(df: pd.DataFrame) -> list[pd.DataFrame]:
    """
    אופציונלי: מחלק DataFrame לעוד DataFrames אם יש המון עמודות (נגיד מעל 15).
    כל מקטע יקבל עד MAX_COLS_PER_TABLE עמודות.
    מחזיר רשימה של DataFrame-ים מפוצלים.
    """
    all_cols = list(df.columns)
    if len(all_cols) <= MAX_COLS_PER_TABLE:
        return [df]

    # פיצול
    chunks = []
    for i in range(0, len(all_cols), MAX_COLS_PER_TABLE):
        cols_chunk = all_cols[i : i + MAX_COLS_PER_TABLE]
        chunk_df = df[cols_chunk].copy()
        chunks.append(chunk_df)
    return chunks


def _prepare_pdf_dataframe(df: pd.DataFrame, format_columns: bool | list[str] = True) -> pd.DataFrame:
    log.debug(f"[PREPARE] Columns at start: {df.columns.tolist()}")

    # 1. המרת תאריכים
    date_cols = [c for c in ("date","closed") if c in df.columns]
    if date_cols:
        log.debug(f"[PREPARE] Coercing date cols {date_cols}")
        df = coerce_dates(df, date_cols)

    # 2. חישובי פיננסים: מתווים net_income, tech_cut, company_net, duration_min, flags
    log.debug("[PREPARE] Enriching financials")
    df = enrich_financials(df)

    # 3. הוספת שורת Totals בראש
    log.debug("[PREPARE] Adding totals row")
    df = append_totals_row(df, position="top")

    # 4. עיצוב עמודות כספיות
    if format_columns:
        log.debug(f"[PREPARE] Formatting currency columns {format_columns}")
        df = format_currency_columns(df, format_columns)

    log.debug(f"[PREPARE] Columns at end: {df.columns.tolist()}")
    return df


def extract_tech_name(df: pd.DataFrame) -> str:
    """
    Extract technician name from DataFrame. Adjust logic as needed for your schema.
    """
    for col in ["tech_name", "technician", "tech"]:
        if col in df.columns:
            val = df[col].dropna().unique()
            if len(val) == 1:
                return str(val[0])
            elif len(val) > 1:
                return ", ".join(map(str, val))
    return ""


def generate_pdf_report(
    df: DataFrame,
    output_path: "Optional[str]" = None,
    report_type: str = "detailed",
    title: "Optional[str]" = None,
    extra: "Optional[dict[str, Any]]" = None,
    chart_path: "Optional[str]" = None,
    format_columns: list[str] | None = None,
    ensure_enriched: bool = True,
    share: float = 0.5,
) -> str:
    log.debug(f"[TYPECHECK] {__name__}.generate_pdf_report → got {type(df).__name__} with shape {getattr(df, 'shape', 'N/A')}")
    log.info("🚀 Starting generate_pdf_report stage")
    try:
        if not isinstance(df, DataFrame):
            log.debug("TYPECHECK: %s in generate_pdf_report", type(df).__name__)
            raise TypeError(f"generate_pdf_report expected DataFrame, got {type(df).__name__}")
        log.debug("TYPECHECK: %s in generate_pdf_report", type(df).__name__)
        log.debug("⚙️ [pdf_generator] generate_pdf_report is active ✅")
        if extra is None:
            extra = {}
        # --- שלב הכנה: העשרה, totals, formatting ---
        if ensure_enriched and "tech_profit" not in df.columns:
            df = enrich(df, share=share)
        df_for_pdf = _prepare_pdf_dataframe(df, format_columns=format_columns)
        # הגנה: ודא שיש לפחות 2 שורות אמיתיות (לא רק totals)
        if df_for_pdf.empty or df_for_pdf["job_id"].nunique() <= 1:
            log.debug("🧾 df_for_pdf.head():\n%s", df_for_pdf.head().to_string())
            raise ValueError("Generated PDF will be empty – skipping")
        # הכנת גרף הכנסות יומי לשילוב בדוח
        try:
            chart_path = Path("output/temp/daily_income_chart.png")
            df_for_chart = df_for_pdf.copy()
            if "date" not in df_for_chart.columns:
                log.warning("No 'date' column found – inserting today's date for chart")
                df_for_chart["date"] = datetime.today().strftime("%Y-%m-%d")
            df_for_chart = (
                df_for_chart
                .dropna(subset=["date", "total"])
                .groupby("date", as_index=False)["total"]
                .sum()
                .rename(columns={"total": "income"})
            )
            try:
                df_for_chart["income"] = df_for_chart["income"].astype(str)
                save_income_chart(df_for_chart, chart_path)
            except Exception as e:
                log.warning(f"⚠️ Failed to generate daily income chart: {e}")
        except Exception as e:
            log.warning("Failed to generate daily income chart: %s", e)
            chart_path = None
        if df_for_pdf.empty:
            raise PDFReportError("DataFrame ריק - אין נתונים ליצירת דוח.")
        n_cols = len(df_for_pdf.columns)
        orientation = "P"
        max_cols = MAX_COLS_PORTRAIT
        if n_cols > MAX_COLS_PORTRAIT:
            orientation = "L"
            max_cols = n_cols
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_DIR, f"{report_type}_report_{timestamp}.pdf")
        pdf = FPDF(orientation=orientation, unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)
        # --- פונט Unicode ---
        pdf.add_font('DejaVu', '', 'static/fonts/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 14)
        log.debug("PDF FONT: %s loaded from %s", pdf.font_family, 'static/fonts/DejaVuSans.ttf')
        client_id = extra.get("client_id")
        if client_id:
            _add_logo(pdf, client_id)
        else:
            pdf.set_xy(PAGE_MARGIN, 15)
        if not title:
            title = f"{report_type.capitalize()} Report"
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 15, title, ln=True, align="C")
        pdf.ln(5)
        df_chunks = _split_columns_if_needed(df_for_pdf)
        for idx, chunk_df in enumerate(df_chunks):
            if idx > 0:
                pdf.add_page()
                pdf.set_xy(PAGE_MARGIN, 15)
                pdf.set_font('DejaVu', '', 14)
                pdf.cell(0, 10, f"Table {idx+1}", ln=True, align="L")
                pdf.ln(5)
            printable_width = pdf.w - 2 * PAGE_MARGIN
            columns = list(chunk_df.columns)
            col_widths = _calculate_col_widths(columns, printable_width, max_cols)
            _print_table_header(pdf, columns, col_widths, font_name='DejaVu')
            _print_full_table(pdf, chunk_df, col_widths, font_name='DejaVu')
        # --- Embed daily income chart if generated ---
        if chart_path and chart_path.is_file():
            pdf.add_page()
            pdf.set_font('DejaVu', '', 14)
            pdf.cell(0, 10, "Daily Income Chart", ln=True, align="C")
            pdf.ln(5)
            pdf.image(str(chart_path), w=180)
        pdf.output(output_path)
        # Debug info before integrity check
        log.debug("🧾 בדיקה אחרונה לפני validate: columns=%s, rows=%d", df_for_pdf.columns.tolist(), len(df_for_pdf))
        try:
            log.debug("🧪 PDF file size: %s bytes", Path(output_path).stat().st_size)
        except Exception as e:
            log.debug("🧪 Could not get PDF file size: %s", e)
        log.debug("🧪 PDF saved to: %s", output_path)
        log.debug("🧪 Columns in df_for_pdf: %s", df_for_pdf.columns.tolist())
        log.debug("🧪 Rows in df_for_pdf: %s", len(df_for_pdf))
        # --- Validate report integrity ---
        validate_report_integrity(Path(output_path), df_for_pdf)
        # --- Add to manifest ---
        if not isinstance(df_for_pdf, pd.DataFrame):
            raise TypeError(f"❌ df passed to manifest is {type(df_for_pdf)}, expected DataFrame")
        tech_name = extract_tech_name(df)
        if not tech_name:
            tech_name = extra.get("tech_name", "")
        log.info(f"📦 PDF Generator: df_for_pdf type = {type(df_for_pdf)}, columns = {getattr(df_for_pdf, 'columns', 'אין')}")
        print(f"⚠️ DEBUG df_for_pdf type = {type(df_for_pdf)}")
        add_report_to_manifest(
            df=df_for_pdf,
            report_path=output_path,
            created_at=datetime.utcnow().isoformat(),
            client_id=extra.get("client_id", "unknown"),
            tech_name=extra.get("tech_name", "unknown"),
            report_type=report_type,
        )
        log.info(f"[📄 Manifest] Saved entry for {report_type} → {output_path}")
        log.info(f"✅ generate_pdf_report complete → {df.shape}")
        return output_path
    except Exception as e:
        log.exception(f"[ERROR] Failed inside generate_pdf_report – {e}")
        log.debug(f"[DF] Columns: {getattr(df, 'columns', [])}")
        log.debug(f"[DF] Head:\n{getattr(df, 'head', lambda x=3: 'N/A')(3)}")
        raise


def generate_excel_report(
    df: "pd.DataFrame",
    output_path: "Optional[str]" = None,
    report_type: str = "detailed",
) -> str:
    """
    מייצר קובץ Excel בודד מתוך DataFrame.
    """
    if df.empty:
        raise PDFReportError("DataFrame ריק - אין נתונים ליצירת דוח.")

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"{report_type}_report_{timestamp}.xlsx")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=report_type.capitalize())

    return output_path


def generate_cfo_report(
    summary_dict: dict,
    output_path: str,
    title: str = "CFO Summary Report",
    date_range: Any = None,
    detail_df: Any = None,
) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C")

    if date_range:
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"Date Range: {date_range}", ln=True)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "KPI Summary", ln=True)

    summary = summary_dict.get("overall", pd.DataFrame())
    if not summary.empty:
        for _, row in summary.iterrows():
            metric, value = row["metric"], row["value"]
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, f"{metric}: {value}", ln=True)

    # Insights Section
    if detail_df is not None:
        engine = InsightsEngine()
        insights = engine.generate(detail_df)
        if insights:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "\ud83d\udccc Observations", ln=True)
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 11)
            severity_color = {
                "INFO": (0, 0, 0),
                "WARNING": (255, 140, 0),
                "CRITICAL": (220, 0, 0),
            }
            for i, ins in enumerate(insights, 1):
                r, g, b = severity_color.get(ins.severity, (0, 0, 0))
                pdf.set_text_color(r, g, b)
                pdf.multi_cell(0, 8, f"{i}. {ins.message}")
                if ins.severity == "CRITICAL":
                    create_action_item(
                        ins, origin="CFO Report", source_file=output_path
                    )
            pdf.set_text_color(0, 0, 0)

    # Save charts temporarily and embed
    charts_dir = Path("output/charts")
    charts_dir.mkdir(parents=True, exist_ok=True)

    def plot_and_embed(
        df: pd.DataFrame, x: str, y: str, chart_title: str, filename: str
    ) -> None:
        plt.figure(figsize=(6, 3))
        plt.bar(df[x], df[y])
        plt.xticks(rotation=45)
        plt.title(chart_title)
        path = charts_dir / filename
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        pdf.image(str(path), w=180)
        pdf.ln(5)

    if "daily" in summary_dict:
        daily_df = summary_dict["daily"]
        if "net_income" in daily_df.columns:
            plot_and_embed(
                daily_df,
                "date",
                "net_income",
                "Daily Net Income",
                "net_income_chart.png",
            )
        if "tax_collected" in daily_df.columns:
            plot_and_embed(
                daily_df, "date", "tax_collected", "Daily Tax", "tax_chart.png"
            )

    if "flags" in summary_dict:
        flag_df = summary_dict["flags"]
        if not flag_df.empty and "flag_type" in flag_df.columns:
            counts = flag_df["flag_type"].value_counts().reset_index()
            counts.columns = ["flag", "count"]
            plt.figure(figsize=(4, 4))
            plt.pie(
                counts["count"],
                labels=counts["flag"],
                autopct="%1.1f%%",
                startangle=140,
            )
            path = charts_dir / "flags_pie.png"
            plt.savefig(path)
            plt.close()
            pdf.image(str(path), w=120)

    pdf.output(output_path)
    log.info(f"✅ CFO Report saved to {output_path}")

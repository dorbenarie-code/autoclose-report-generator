# components/reports_table_component.py

import os
from datetime import datetime
from typing import List, Dict

import dash_bootstrap_components as dbc
from dash import html
from myapp.utils.date_utils import parse_date_flex

CLIENT_REPORTS_FOLDER = "backup/client_reports"


def get_reports_data() -> List[Dict[str, str]]:
    """
    Scan the CLIENT_REPORTS_FOLDER and extract report info based on filename structure.

    Filename pattern expected: "monthly_summary_YYYY-MM-DD_to_YYYY-MM-DD.pdf"
    Example: "monthly_summary_2025-05-01_to_2025-05-31.pdf"

    Returns:
        List[Dict[str, str]]: List of reports, each containing:
            - "name": Display name for UI (e.g., "Monthly Report (2025-05-01 – 2025-05-31)")
            - "date_range": The date range string (e.g., "2025-05-01 – 2025-05-31")
            - "filename": The actual filename on disk
    """
    reports: List[Dict[str, str]] = []

    if not os.path.isdir(CLIENT_REPORTS_FOLDER):
        return reports

    for filename in os.listdir(CLIENT_REPORTS_FOLDER):
        if not filename.endswith(".pdf") or not filename.startswith("monthly_summary_"):
            continue

        try:
            date_part = filename.removeprefix("monthly_summary_").removesuffix(".pdf")
            if "_to_" in date_part:
                start_str, end_str = date_part.split("_to_")
                start_date = parse_date_flex(start_str).date()
                end_date = parse_date_flex(end_str).date()
                display_range = f"{start_date} – {end_date}"
            else:
                display_range = date_part
            reports.append(
                {
                    "name": f"Monthly Report ({display_range})",
                    "date": display_range,
                    "filename": filename,
                }
            )
        except Exception:
            continue

    def sort_key(item: Dict[str, str]) -> datetime:
        try:
            start_str = item["date"].split(" – ")[0]
            return parse_date_flex(start_str)
        except Exception:
            return datetime.min

    return sorted(reports, key=sort_key, reverse=True)


def build_reports_table() -> html.Div:
    """
    Build a styled Bootstrap table displaying reports with name, date range, and a download button.
    Includes a floating help button with tooltip for user guidance.

    Returns:
        html.Div: A Dash HTML Div containing the help button and the table.
    """
    reports = get_reports_data()

    # Floating help button (top right)
    help_btn_id = "reports-table-help-btn"
    help_button = html.Div(
        [
            dbc.Button(
                html.I(
                    className="bi bi-question-circle",
                    style={"fontSize": "1.3em"},
                    aria_label="Help",
                ),
                id=help_btn_id,
                color="light",
                outline=True,
                size="sm",
                style={
                    "position": "absolute",
                    "top": "-18px",
                    "right": "-8px",
                    "zIndex": 10,
                    "borderRadius": "50%",
                    "boxShadow": "0 2px 8px rgba(44,62,80,0.10)",
                    "padding": "6px 9px",
                },
            ),
            dbc.Tooltip(
                "This table lists all available monthly reports. Click 'Download' to save a PDF.",
                target=help_btn_id,
                placement="left",
                style={"fontSize": "0.98em"},
            ),
        ],
        style={"position": "relative", "height": "0px"},
    )

    header = html.Thead(
        html.Tr(
            [
                html.Th(
                    "#", style={"fontWeight": "bold", "color": "#2c3e50", "width": "4%"}
                ),
                html.Th(
                    [
                        "📄 Report Name ",
                    ],
                    style={"fontWeight": "bold", "color": "#2c3e50"},
                ),
                html.Th(
                    "📆 Date Range", style={"fontWeight": "bold", "color": "#2c3e50"}
                ),
                html.Th(
                    "⬇️ Download",
                    className="text-center",
                    style={"fontWeight": "bold", "color": "#2c3e50"},
                ),
            ]
        ),
        className="thead-light",
    )

    body_rows = []
    for idx, report in enumerate(reports):
        btn_id = f"download-btn-{idx}"
        body_rows.append(
            html.Tr(
                [
                    html.Td(
                        str(idx + 1),
                        style={
                            "fontWeight": "bold",
                            "color": "#888",
                            "textAlign": "center",
                        },
                    ),
                    html.Td(
                        [
                            report["name"],
                            dbc.Badge(
                                "PDF",
                                color="danger",
                                pill=True,
                                className="ms-2",
                                style={"fontSize": "0.8em"},
                            ),
                        ],
                        style={"padding": "10px 16px"},
                    ),
                    html.Td(
                        [
                            html.I(
                                className="bi bi-calendar3 me-1",
                                style={"color": "#6c757d", "fontSize": "1.1em"},
                                aria_label="Date",
                            ),
                            html.Span(report["date"], style={}),
                            html.Span(" (report date)", className="visually-hidden"),
                        ],
                        style={"padding": "10px 16px"},
                    ),
                    html.Td(
                        [
                            dbc.Button(
                                [
                                    html.I(
                                        className="bi bi-download me-1",
                                        style={"color": "#375a7f", "fontSize": "1.1em"},
                                        aria_label="Download",
                                    ),
                                    html.Span("Download"),
                                    html.Span(
                                        " (download report)",
                                        className="visually-hidden",
                                    ),
                                ],
                                id=btn_id,
                                color="primary",
                                size="sm",
                                href=f"/download/{report['filename']}",
                                target="_blank",
                                style={
                                    "borderRadius": "8px",
                                    "fontWeight": "600",
                                    "boxShadow": "0 2px 8px rgba(44,62,80,0.08)",
                                    "padding": "6px 14px",
                                },
                            ),
                            dbc.Tooltip(
                                "Download PDF report",
                                target=btn_id,
                                placement="top",
                                style={"fontSize": "0.95em"},
                            ),
                        ],
                        className="text-center",
                        style={"padding": "10px 16px"},
                    ),
                ],
                className="table-row-hover",
            )
        )

    table = dbc.Table(
        children=[header, html.Tbody(body_rows)],
        bordered=True,
        hover=True,
        responsive=True,
        className="align-middle shadow-sm",
        style={
            "backgroundColor": "#fff",
            "borderRadius": "14px",
            "boxShadow": "0 2px 8px rgba(44,62,80,0.08)",
            "fontFamily": "Segoe UI, Arial, sans-serif",
            "overflow": "hidden",
        },
    )

    return html.Div([help_button, table], style={"position": "relative"})

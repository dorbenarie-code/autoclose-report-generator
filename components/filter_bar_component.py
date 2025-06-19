from dash import dcc, html
from myapp.dashboard.data_loader import get_filter_options
from typing import Any, List, Dict, Sequence
from typing import cast


def build_filter_bar() -> html.Div:
    """
    Renders a top filter bar with technician, date range and report type dropdowns.
    Populates dropdowns dynamically from CSV data.
    """
    technician_options, report_type_options = get_filter_options()

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("🔧 טכנאי"),
                            dcc.Dropdown(
                                id="technician-filter",
                                options=technician_options,  # type: ignore[arg-type]
                                placeholder="בחר טכנאי",
                                multi=True,
                            ),
                        ],
                        className="col-md-4",
                    ),
                    html.Div(
                        [
                            html.Label("📆 טווח תאריכים"),
                            dcc.DatePickerRange(
                                id="date-range-filter",
                                start_date_placeholder_text="מתאריך",
                                end_date_placeholder_text="עד תאריך",
                            ),
                        ],
                        className="col-md-4",
                    ),
                    html.Div(
                        [
                            html.Label("📂 סוג דוח"),
                            dcc.Dropdown(
                                id="report-type-filter",
                                options=report_type_options,  # type: ignore[arg-type]
                                placeholder="בחר סוג דוח",
                                multi=True,
                            ),
                        ],
                        className="col-md-4",
                    ),
                ],
                className="row gy-3",
            ),
        ],
        className="container my-4",
    )

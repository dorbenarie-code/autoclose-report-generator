# dashboard/callbacks/dashboard_callbacks.py

import os
import pandas as pd
from dash import Output, Input, callback, dcc, html
from dash.exceptions import PreventUpdate
from components.kpi_cards_component import build_kpi_cards
from myapp.dashboard.data_loader import load_dashboard_data
from components.toast_component import build_toast
from typing import Any

# Path to the merged jobs CSV – can be overridden if needed
MERGED_CSV_PATH = os.path.join("output", "merged_jobs.csv")


def register_callbacks(app: Any) -> None:
    # future logic for callbacks
    pass


def register_theme_callback(app: Any) -> None:
    # future theming logic
    pass


@callback(
    Output("kpi-cards", "children"),
    Input("main-dashboard-container", "children"),  # triggers on page load
)
def update_kpi_cards(_: Any) -> Any:
    """
    Loads the merged_jobs.csv file and updates the KPI cards with:
    - Total number of reports
    - Unique active technicians
    - Total service amount (fallback to 0.0 if 'amount' column doesn't exist)
    """
    # Try to read the merged CSV; if missing or empty, do nothing (PreventUpdate)
    try:
        df = pd.read_csv(MERGED_CSV_PATH)
    except FileNotFoundError:
        raise PreventUpdate("merged_jobs.csv not found – skipping KPI update.")

    if df.empty:
        raise PreventUpdate("merged_jobs.csv is empty – skipping KPI update.")

    # Calculate total reports
    total_reports = len(df)

    # Calculate unique technicians if column present
    active_technicians = df["technician"].nunique() if "technician" in df.columns else 0

    # Calculate total amount if column present
    total_amount = df["amount"].sum() if "amount" in df.columns else 0.0

    # Return updated KPI cards
    return build_kpi_cards(
        total_reports=total_reports,
        active_technicians=active_technicians,
        total_amount=total_amount,
    )


@callback(
    Output("toast-container", "children"),
    Input("url", "pathname"),  # אם אתה משתמש ב־dcc.Location
)
def show_toast_on_load(pathname: Any) -> Any:
    try:
        df = load_dashboard_data()
        if df.empty:
            return build_toast(
                "⚠️ הקובץ לא מכיל נתונים – בדוק אם חסר או לא תקין", category="danger"
            )
        if df["technician"].isna().all():
            return build_toast(
                "⚠️ אין עמודת טכנאי – חלק מהגרפים לא יוצגו", category="warning"
            )
        if df["job_type"].isna().all():
            return build_toast(
                "⚠️ אין סוגי עבודות – יתכן ודוחות מסוימים לא יעבדו", category="warning"
            )
    except Exception as e:
        return build_toast(f"שגיאה בטעינת הדאטה: {str(e)}", category="danger")

    raise PreventUpdate

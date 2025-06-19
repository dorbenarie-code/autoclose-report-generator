# dashboard/layouts/main_layout.py

from dash import html
from components.forms.upload_form_component import render_upload_form
from components.cards.kpi_cards_component import build_kpi_cards
from components.graphs.graphs_component import render_jobs_per_technician_chart


def render_main_layout() -> html.Div:
    """
    Builds the main layout of the AutoClose dashboard:
    - Upload form at the top
    - KPI cards with summary stats
    - Bar chart showing jobs per technician
    - Placeholder for future tables
    """
    # נשארים עם ערכי ה־KPI placeholders
    # (אם הם כבר נטענים מדאטה חיצוני דרך callback - אין שינוי)
    total_reports_value = 87
    active_technicians_value = 12
    total_amount_value = 19230.75

    return html.Div(
        id="main-dashboard-container",
        className="container-fluid py-4",
        children=[
            # HEADER
            html.Div(
                className="d-flex justify-content-between align-items-center mb-4",
                children=[
                    html.H2("AutoClose Dashboard", className="mb-0"),
                    html.Div(
                        id="last-updated",
                        className="text-muted small",
                        children="Last updated: --",
                    ),
                ],
            ),
            # UPLOAD FORM
            render_upload_form(),
            html.Hr(className="my-4"),
            # KPI CARDS – still with placeholders (or updated via callback)
            html.Div(
                id="kpi-cards",
                children=build_kpi_cards(
                    total_reports=total_reports_value,
                    active_technicians=active_technicians_value,
                    total_amount=total_amount_value,
                ),
            ),
            # CHARTS & TABLES SECTION
            html.Div(
                id="charts-tables-section",
                className="row g-4",
                children=[
                    # Graph: Jobs per technician
                    html.Div(
                        id="graphs-container",
                        className="col-12 mb-4",
                        children=render_jobs_per_technician_chart(),
                    ),
                    # Future tables placeholder
                    html.Div(id="tables-container", className="col-12"),
                ],
            ),
        ],
    )

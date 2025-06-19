# layout_utils.py

from dash import html, dcc
import dash_bootstrap_components as dbc
from plotly.graph_objects import Figure
import pandas as pd
from components.reports_table_component import build_reports_table
from components.navbar_component import build_navbar
from components.footer_component import build_footer
from components.theme_toggle_component import build_theme_toggle
from components.kpi_cards_component import build_kpi_cards
from myapp.dashboard.data_loader import get_kpi_metrics, get_filter_options
from components.tabs_component import build_dashboard_tabs
from components.filter_bar_component import build_filter_bar
from components.email_sender_component import build_email_sender_ui
from components.email_log_component import build_email_log_component


def build_dashboard_layout(fig: Figure, df: pd.DataFrame) -> html.Div:
    """
    Build the full HTML layout for the interactive dashboard, including header, filters area,
    graph card, and footer.

    Args:
        fig (Figure): A Plotly Figure to render in the main chart area.
        df (pd.DataFrame): DataFrame containing the job data (for filter defaults).

    Returns:
        html.Div: The root Div containing all dashboard components.
    """
    # Location component for future navigation/routing
    url_location = dcc.Location(id="url", refresh=False)

    # Meta viewport tag for responsive behavior if exporting as standalone HTML
    meta_viewport = html.Meta(
        name="viewport", content="width=device-width, initial-scale=1"
    )

    # Header section: title, divider, and subtitle
    header = html.Div(
        [
            html.H1(
                "📊 Technician Report Dashboard",
                className="display-4 text-center",
                style={
                    "marginBottom": "10px",
                    "fontWeight": "bold",
                    "color": "#2c3e50",
                },
            ),
            html.Hr(
                style={
                    "borderTop": "2px solid #bbbbbb",
                    "width": "50px",
                    "margin": "10px auto",
                }
            ),
            html.H2(
                "Total Jobs by Technician and Job Type",
                className="lead text-center text-muted",
                style={"marginBottom": "30px"},
            ),
        ],
        id="dashboard-header",
        className="py-4",
        style={"backgroundColor": "#f8f9fa"},
    )

    # Filters area with DatePickerRange and job_type Dropdown
    filters = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dcc.DatePickerRange(
                            id="date-range-picker-kpi",
                            min_date_allowed=df["date"].min(),
                            max_date_allowed=df["date"].max(),
                            start_date=df["date"].min(),
                            end_date=df["date"].max(),
                            display_format="YYYY-MM-DD",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="job-type-dropdown",
                            options=[
                                {"label": jt.capitalize(), "value": jt}
                                for jt in df["job_type"].unique()
                            ],
                            placeholder="Select job type",
                        ),
                        width=6,
                    ),
                ]
            )
        ],
        id="dashboard-filters",
        className="mb-4",
        style={"maxWidth": "800px", "margin": "0 auto"},
    )

    # Graph card wrapped in Bootstrap Card component
    graph_card = dbc.Card(
        dbc.CardBody(
            [
                dcc.Graph(
                    id="technician-job-type-histogram",
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "600px"},
                )
            ]
        ),
        className="shadow",
        style={
            "marginBottom": "40px",
            "borderRadius": "18px",
            "border": "1px solid #eaeaea",
            "backgroundColor": "#fff",
        },
    )

    # Container for the graph card to ensure responsive margins
    graph_section = dbc.Container(graph_card, id="dashboard-graph-section")

    # KPI metrics and cards
    total_reports, active_techs, total_amount = get_kpi_metrics()
    kpi_cards = build_kpi_cards(total_reports, active_techs, total_amount)
    tech_options, report_options = get_filter_options()
    filter_bar = build_filter_bar(tech_options, report_options)
    tabs = build_dashboard_tabs()

    # Assemble full layout
    layout = html.Div(
        children=[
            html.Div(id="toast-container"),  # Toasts will be rendered here
            build_navbar(),
            html.Div(
                className="container mt-5",
                children=[
                    kpi_cards,
                    filter_bar,
                    tabs,
                    html.Div(
                        id="dashboard-tab-content",
                        children=[
                            dcc.Graph(id="main-graph", figure=fig),
                            html.Div(id="exported-reports-container", className="mt-4"),
                            build_email_sender_ui(),
                            build_email_log_component(),
                        ],
                    ),
                ],
            ),
            url_location,
            meta_viewport,
            header,
            filters,
            graph_section,
            html.Hr(style={"marginTop": "40px", "marginBottom": "40px"}),
            html.H3(
                "📁 דוחות אחרונים",
                className="text-center mb-4",
                style={"color": "#2c3e50", "fontWeight": "bold"},
            ),
            dbc.Container(build_reports_table(), style={"paddingBottom": "40px"}),
            build_footer(),
        ],
        style={
            "fontFamily": "Arial, sans-serif",
            "backgroundColor": "#ffffff",
            "paddingTop": "80px",
        },
    )

    return layout

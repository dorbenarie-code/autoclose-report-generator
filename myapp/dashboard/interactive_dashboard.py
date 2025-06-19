import os
import logging

from dash import Dash, html
import dash_bootstrap_components as dbc
from flask import Flask

from myapp.dashboard.data_loader import load_dashboard_data
from components.graphs.jobs_per_technician import render_jobs_per_technician_chart
from components.graphs.jobs_trend import render_jobs_trend_chart
from components.graphs.service_type_pie import render_service_type_pie
from components.graphs.activity_heatmap import render_activity_heatmap
from components.filter_bar_component import build_filter_bar


logger = logging.getLogger(__name__)


def create_dashboard(server: Flask) -> Dash:
    """
    Initialize and return a Dash app attached to the given Flask server.
    Includes all dynamic graphs and fallback logic.
    """
    external_stylesheets = [dbc.themes.BOOTSTRAP]

    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname="/dashboard/",
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True,
    )
    dash_app.title = "AutoClose Dashboard"

    # 1. Load data
    csv_path = os.getenv("CSV_PATH", "output/merged_jobs.csv")
    logger.info(f"📄 Loading dashboard data from: {csv_path}")

    try:
        df = load_dashboard_data(csv_path)
    except Exception as e:
        logger.warning(f"⚠️ Failed to load dashboard data: {e}")
        df = None

    # 2. Fallback layout if no data
    if df is None or df.empty:
        logger.warning("🚫 No valid data for dashboard. Showing fallback screen.")
        dash_app.layout = dbc.Container(
            [
                dbc.Row(
                    dbc.Col(
                        [
                            html.H2(
                                "📄 No Data Available", className="text-center my-3"
                            ),
                            html.P(
                                "Please upload a valid CSV file with the required columns.",
                                className="text-center",
                                style={"fontSize": "18px"},
                            ),
                        ],
                        width=12,
                    ),
                    className="mt-5",
                )
            ],
            fluid=True,
            className="bg-light vh-100",
        )
        return dash_app

    # 3. MAIN DASHBOARD LAYOUT
    dash_app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "📊 AutoClose Technician Dashboard",
                        className="my-4 text-center",
                    ),
                    build_filter_bar(),
                    html.Div(id="graphs-container"),
                    html.Div(id="toast-container"),
                ],
                className="container",
            )
        ]
    )

    return dash_app

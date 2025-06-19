import pandas as pd
from dash import Output, Input, State, callback, html
import dash_bootstrap_components as dbc

from myapp.dashboard.data_loader import load_dashboard_data
from components.graphs.jobs_per_technician import render_jobs_per_technician_chart
from components.graphs.jobs_trend import render_jobs_trend_chart
from components.graphs.service_type_pie import render_service_type_pie
from components.graphs.activity_heatmap import render_activity_heatmap
from components.tables.summary_table import render_summary_table


@callback(
    Output("graphs-container", "children"),
    Input("technician-filter", "value"),
    Input("date-range-filter", "start_date"),
    Input("date-range-filter", "end_date"),
    Input("report-type-filter", "value"),
)
def update_graphs(technicians, start_date, end_date, report_types):
    """
    Callback to filter the data according to the user's selected filters
    (technicians, date range, report types), then render the relevant graphs.

    If the resulting dataframe is empty or invalid, we show a fallback alert
    explaining that there's no data to display under these filters.
    """
    # 1. Load and filter data
    df = load_dashboard_data()

    # If df is empty after load, return a fallback
    if df.empty:
        return dbc.Alert(
            "No data available under these filters (or in general).",
            color="warning",
            className="my-3",
        )

    # Filter by technician
    if technicians:
        if "technician" in df.columns:
            df = df[df["technician"].isin(technicians)]
        else:
            # If 'technician' column doesn't exist, no sense filtering
            return dbc.Alert(
                "Technician filter selected but 'technician' column is missing.",
                color="warning",
                className="my-3",
            )

    # Filter by report type
    if report_types:
        if "job_type" in df.columns:
            df = df[df["job_type"].isin(report_types)]
        else:
            return dbc.Alert(
                "Report type filter selected but 'job_type' column is missing.",
                color="warning",
                className="my-3",
            )

    # Filter by date range
    if "date" in df.columns:
        if start_date:
            df = df[df["date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date)]
    else:
        # If there's no 'date' column, we can't do date filtering
        return dbc.Alert(
            "Date range filter applied but 'date' column is missing.",
            color="warning",
            className="my-3",
        )

    # 2. If the DataFrame is empty after filtering, show fallback
    if df.empty:
        return dbc.Alert(
            "No data matches your current filter selections.",
            color="info",
            className="my-3",
        )

    # 3. Render the graphs with the filtered df
    return html.Div(
        [
            render_jobs_per_technician_chart(df),
            render_jobs_trend_chart(df),
            render_service_type_pie(df),
            render_activity_heatmap(df),
            render_summary_table(df),
        ],
        className="mt-3",
    )

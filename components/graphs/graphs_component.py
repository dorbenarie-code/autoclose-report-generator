# components/graphs/graphs_component.py

import os
import pandas as pd
import plotly.express as px
from dash import dcc, html
from myapp.dashboard.data_loader import load_dashboard_data

# Path to the merged jobs data
MERGED_CSV_PATH = os.path.join("output", "merged_jobs.csv")


def render_jobs_per_technician_chart() -> html.Div:
    """
    Generates a bar chart of number of jobs per technician.
    Reads data from merged_jobs.csv, handles missing file, missing column,
    empty data, and unexpected read errors.
    """
    try:
        df = load_dashboard_data(MERGED_CSV_PATH)
    except Exception as e:
        return html.Div(
            dcc.Markdown(f"⚠️ שגיאה בקריאת הנתונים: {e}"),
            id="jobs-per-technician-error",
            className="text-danger",
        )

    if df.empty or "technician" not in df.columns:
        return html.Div(
            dcc.Markdown("⚠️ עמודת טכנאי חסרה או שאין נתונים זמינים."),
            id="jobs-per-technician-error",
            className="text-warning",
        )

    tech_series = df["technician"].dropna()
    if tech_series.empty:
        return html.Div(
            dcc.Markdown("ℹ️ אין רשומות פעילות להצגה."),
            id="jobs-per-technician-empty",
            className="text-muted",
        )

    job_counts = tech_series.value_counts().reset_index()
    job_counts.columns = ["Technician", "Jobs"]

    fig = px.bar(
        job_counts,
        x="Technician",
        y="Jobs",
        title="Jobs per Technician",
        text="Jobs",
        labels={"Jobs": "מספר עבודות", "Technician": "טכנאי"},
        template="simple_white",
    )
    fig.update_traces(marker_color="steelblue", textposition="outside")
    fig.update_layout(margin=dict(t=50, b=40), xaxis_tickangle=-45)

    return html.Div(
        dcc.Graph(
            id="jobs-per-technician-chart",
            figure=fig,
            config={"displayModeBar": False, "responsive": True},
        ),
        id="jobs-per-technician-container",
        className="mb-4",
    )

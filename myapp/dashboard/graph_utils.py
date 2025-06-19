# graph_utils.py

import pandas as pd
import plotly.express as px
from typing import Set
from plotly.graph_objects import Figure


def create_technician_histogram(df: pd.DataFrame) -> Figure:
    """
    Create a grouped bar chart showing job count per technician by job type.

    Args:
        df (pd.DataFrame): DataFrame containing 'technician' and 'job_type' columns.

    Returns:
        Figure: Plotly Figure object representing the histogram.

    Raises:
        ValueError: If required columns are missing in the DataFrame.
    """
    # Validate required columns
    required_columns: Set[str] = {"technician", "job_type"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Cannot create histogram. Missing columns: {missing_columns}")

    # Create histogram figure
    fig = px.histogram(
        df,
        x="technician",
        color="job_type",
        barmode="group",
        title="Number of Jobs per Technician by Job Type",
        labels={
            "technician": "Technician",
            "job_type": "Job Type",
            "count": "Number of Jobs",
        },
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    # קיבוע סדר הקטגוריות בציר X לפי סדר הופעה ב־DataFrame
    fig.update_xaxes(
        categoryorder="array", categoryarray=list(df["technician"].unique())
    )
    # עיצוב מודרני
    fig.update_layout(
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="Job Type",
        xaxis_title="Technician",
        yaxis_title="Number of Jobs",
        bargap=0.18,
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        font=dict(family="Segoe UI, Arial, sans-serif", size=16, color="#222"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#eaeaea",
            borderwidth=1,
        ),
        title=dict(
            x=0.5,
            font=dict(size=22, family="Segoe UI, Arial, sans-serif", color="#2c3e50"),
        ),
    )
    fig.update_traces(marker_line_width=1.5, marker_line_color="#eaeaea")

    return fig

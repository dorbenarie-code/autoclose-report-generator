import os
import pandas as pd
import plotly.express as px
from dash import dcc, html
import dash_bootstrap_components as dbc


def render_activity_heatmap(df: pd.DataFrame) -> html.Div:
    """
    Renders a heatmap showing job activity across days of the week and hours.
    df: DataFrame שכבר נטען מראש (לא טוען אותו כאן)
    Fallback & Error Handling:
    - If data load fails -> Shows a danger alert.
    - If 'timestamp' column is missing/invalid -> Shows a warning alert.
    - If after filtering no valid timestamps remain -> Shows an info alert.
    """
    # 1. Validate 'timestamp' availability
    if (
        df is None
        or df.empty
        or "timestamp" not in df.columns
        or df["timestamp"].dropna().empty
    ):
        return dbc.Alert(
            "⚠️ No usable 'timestamp' data for heatmap.",
            color="warning",
            className="m-3",
        )

    # 2. Clean/prepare timestamps
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df.dropna(subset=["timestamp"], inplace=True)
    if df.empty:
        return dbc.Alert(
            "ℹ️ No valid timestamps after cleaning data.", color="info", className="m-3"
        )

    # 3. Extract Hour & Weekday
    df["Hour"] = df["timestamp"].dt.hour
    df["Weekday"] = df["timestamp"].dt.day_name()

    # 4. Group by (Weekday, Hour)
    heatmap_data = df.groupby(["Weekday", "Hour"]).size().reset_index(name="Jobs")
    if heatmap_data.empty:
        return dbc.Alert(
            "ℹ️ No activity data available for heatmap.", color="info", className="m-3"
        )

    # 5. Plotly Heatmap
    fig = px.density_heatmap(
        heatmap_data,
        x="Hour",
        y="Weekday",
        z="Jobs",
        title="🕒 Activity Heatmap – Jobs by Hour & Day",
        color_continuous_scale="Viridis",
        labels={"Jobs": "Job Count"},
        nbinsx=24,  # 24 bins to align hours 0-23
    )

    # Order weekdays from Sunday->Saturday (or any custom order)
    fig.update_layout(
        margin=dict(t=60, b=50, l=30, r=30),
        yaxis=dict(
            categoryorder="array",
            categoryarray=[
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ],
        ),
    )

    # 6. Return as a styled component
    return dbc.Card(
        [
            dbc.CardHeader("Jobs Activity Heatmap"),
            dbc.CardBody(
                dcc.Graph(
                    id="activity-heatmap-chart",
                    figure=fig,
                    config={"displayModeBar": False, "responsive": True},
                    style={"height": "500px"},
                )
            ),
        ],
        className="mb-4 shadow-sm",
    )

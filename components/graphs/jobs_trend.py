import plotly.express as px
import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc


def render_jobs_trend_chart(df: pd.DataFrame) -> html.Div:
    """
    Renders a line chart showing the monthly trend of job volume.
    df: DataFrame שכבר נטען מראש (לא טוען אותו כאן)
    Fallback & Error Handling:
    - If data load fails -> Shows a red (danger) alert.
    - If 'date' column is missing/invalid -> Shows a warning alert.
    - If there's no data to plot -> Info alert.
    """
    # 1. Validate date availability
    if df is None or df.empty or "date" not in df.columns or df["date"].isna().all():
        return dbc.Alert(
            "⚠️ No valid 'date' data available for trend analysis.",
            color="warning",
            className="m-3",
        )

    # 2. Group by month
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    trend_df = df.groupby("month").size().reset_index(name="Jobs")

    # 3. If no trend data
    if trend_df.empty:
        return dbc.Alert(
            "ℹ️ No job data to plot over time.", color="info", className="m-3"
        )

    # 4. Create line chart
    fig = px.line(
        trend_df,
        x="month",
        y="Jobs",
        markers=True,
        title="📈 Monthly Job Volume Trend",
        labels={"month": "Month", "Jobs": "Job Count"},
        template="plotly_white",
    )

    fig.update_traces(
        line=dict(color="royalblue", width=3),
        marker=dict(size=8),
        hovertemplate="<b>Month: %{x}</b><br>Jobs: %{y}<extra></extra>",
    )
    fig.update_layout(
        margin=dict(t=60, b=50, l=30, r=30), xaxis_tickangle=-45, hovermode="x unified"
    )

    # 5. Wrap in a styled component
    return dbc.Card(
        [
            dbc.CardHeader("Monthly Job Volume Trend"),
            dbc.CardBody(
                dcc.Graph(
                    id="jobs-trend-chart",
                    figure=fig,
                    config={"displayModeBar": False, "responsive": True},
                    style={"height": "400px"},
                )
            ),
        ],
        className="mb-4 shadow-sm",
    )

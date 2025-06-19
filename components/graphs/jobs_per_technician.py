import plotly.express as px
import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc


def render_jobs_per_technician_chart(df: pd.DataFrame) -> html.Div:
    """
    Renders a bar chart showing the number of jobs completed per technician.
    df: DataFrame שכבר נטען מראש (לא טוען אותו כאן)
    התנהגות fallback:
    - אם קרתה שגיאה בטעינת הדאטה -> מציג התרעה אדומה במקום לגרום לשבירת הממשק.
    - אם חסרה עמודת 'technician' -> מציג התרעה כתומה ("Missing data").
    - אם עמודת 'technician' קיימת אבל ריקה -> מציג הודעת מידע ("No records").
    - אחרת -> מציג גרף עמודות מעוצב.
    """
    # 1. בדוק אם הדאטה חסרה או חסרה עמודה
    if df is None or df.empty or "technician" not in df.columns:
        return dbc.Alert(
            "⚠️ Technician data is missing or empty.", color="warning", className="m-3"
        )

    # 2. בדוק אם יש בכלל רשומות טכנאי
    tech_series = df["technician"].dropna()
    if tech_series.empty:
        return dbc.Alert(
            "ℹ️ No technician job records available.", color="info", className="m-3"
        )

    # 3. חישוב כמות עבודות לכל טכנאי
    job_counts = tech_series.value_counts().reset_index()
    job_counts.columns = ["Technician", "Jobs"]

    # 4. יצירת גרף + עיצוב Plotly
    fig = px.bar(
        job_counts,
        x="Technician",
        y="Jobs",
        title="🔧 Jobs per Technician",
        text="Jobs",
        labels={"Jobs": "Number of Jobs", "Technician": "Technician"},
        template="plotly_white",
    )

    fig.update_traces(
        marker_color="mediumseagreen",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Jobs: %{y}<extra></extra>",
    )
    fig.update_layout(
        margin=dict(t=60, b=50, l=30, r=30),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        xaxis_tickangle=-45,
    )

    # 5. החזרת רכיב Dash עם הגרף
    return dbc.Card(
        [
            dbc.CardHeader("Jobs per Technician"),
            dbc.CardBody(
                dcc.Graph(
                    id="jobs-per-technician-chart",
                    figure=fig,
                    config={"displayModeBar": False, "responsive": True},
                    style={"height": "400px"},  # התאמת גובה הגרף
                )
            ),
        ],
        className="mb-4 shadow-sm",
    )

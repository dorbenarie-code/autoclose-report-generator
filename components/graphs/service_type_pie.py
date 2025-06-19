import plotly.express as px
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd


def render_service_type_pie(df: pd.DataFrame) -> html.Div:
    """
    Renders a donut-style pie chart showing the distribution of service types.
    df: DataFrame שכבר נטען מראש (לא טוען אותו כאן)
    Fallback & Error Handling:
    - If data loading fails -> Shows a danger alert.
    - If no or invalid 'service_type' column -> Shows a warning alert.
    - Otherwise -> Displays a donut chart with dynamic pulls.
    """
    # 1. Validate 'service_type' availability
    if (
        df is None
        or df.empty
        or "service_type" not in df.columns
        or df["service_type"].dropna().empty
    ):
        return dbc.Alert(
            "⚠️ No available 'service_type' data.", color="warning", className="m-3"
        )

    # 2. Prepare data for pie chart
    counts = df["service_type"].value_counts(dropna=True).reset_index()
    counts.columns = ["Service", "Count"]

    # 3. Create donut chart
    fig = px.pie(
        counts,
        names="Service",
        values="Count",
        title="🔧 Service Type Distribution",
        hole=0.4,  # donut style
        color_discrete_sequence=px.colors.qualitative.Safe,
    )

    fig.update_traces(
        textinfo="percent+label",
        pull=[0.05] * len(counts),  # Slight pull for each slice
        hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
    )
    fig.update_layout(
        margin=dict(t=60, b=50, l=30, r=30),
        showlegend=True,
        legend_title_text="Service Type",
    )

    # 4. Return styled component
    return dbc.Card(
        [
            dbc.CardHeader("Service Type Distribution"),
            dbc.CardBody(
                dcc.Graph(
                    id="service-type-pie-chart",
                    figure=fig,
                    config={"displayModeBar": False, "responsive": True},
                    style={"height": "400px"},
                )
            ),
        ],
        className="mb-4 shadow-sm",
    )

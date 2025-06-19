import pandas as pd
from dash import dash_table, html
import dash_bootstrap_components as dbc


def render_summary_table(df: pd.DataFrame) -> html.Div:
    """
    Renders a summary DataTable showing the 10 most recent jobs (sorted by 'date' descending).
    Provides styling, sorting, and fallback handling if columns or data are missing.
    """

    # 1. Fallback if DataFrame is empty
    if df.empty:
        return dbc.Alert(
            "ℹ️ No data available to display.", color="info", className="my-3"
        )

    # 2. Ensure we have 'date' column for sorting
    if "date" in df.columns:
        df = df.sort_values("date", ascending=False).copy()
    else:
        # If there's no date column, we won't sort by date
        pass

    # 3. Show only first 10 records
    df = df.head(10)

    # 4. Decide which columns to display
    # You can adjust or reorder them as you prefer
    columns_to_show = ["job_id", "date", "technician", "service_type", "total"]
    available_cols = [col for col in columns_to_show if col in df.columns]

    if not available_cols:
        return dbc.Alert(
            "⚠️ No relevant columns to display in summary table.",
            color="warning",
            className="my-3",
        )

    # 5. Setup DataTable columns with user-friendly headers
    table_columns = [
        {"name": col.replace("_", " ").capitalize(), "id": col}
        for col in available_cols
    ]

    # 6. Create the table
    table = dash_table.DataTable(
        data=df[available_cols].to_dict("records"),
        columns=table_columns,
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
        style_cell={"textAlign": "center", "padding": "8px"},
        page_size=10,
        sort_action="native",  # Enable user to sort columns
        filter_action="native",  # Optionally, enable filtering in the table
        row_deletable=False,  # If you want users to remove rows, change to True
    )

    # 7. Wrap in a styled container
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5("📋 סיכום עבודות אחרונות", className="mb-0 text-center")
            ),
            dbc.CardBody(table),
        ],
        className="my-4 shadow-sm",
    )

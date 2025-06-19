from dash import html


def build_export_buttons():
    """
    Returns a container with export buttons (Excel and PDF),
    plus an area to show status messages (e.g., success or error).
    """
    return html.Div(
        className="d-flex gap-2 mb-4 align-items-center",
        children=[
            # Excel Export
            html.Button(
                "⬇️ Export to Excel",
                id="export-excel-btn",
                className="btn btn-outline-success",
            ),
            # PDF Export
            html.Button(
                "🖨️ Export to PDF",
                id="export-pdf-btn",
                className="btn btn-outline-primary",
            ),
            # Send by Email
            html.Button(
                "📧 Send by Email",
                id="send-email-btn",
                className="btn btn-outline-dark",
            ),
            # Status messages for exports
            html.Div(
                id="export-excel-status",
                className="text-muted",
                style={"fontSize": "0.9rem"},  # טיפה קטן יותר, משמש כסטטוס
            ),
        ],
    )

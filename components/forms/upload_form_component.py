# upload_form_component.py

from dash import html, dcc


def render_upload_form() -> html.Div:
    """
    Returns a drag-&-drop upload component with:
      - Manual “Select” link
      - Immediate feedback area
      - File-type restriction (CSV/Excel)
      - Clear IDs for callbacks
      - Consistent styling hooks
    """
    return html.Div(
        id="upload-form-container",
        className="mb-4",
        children=[
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        html.Span("Drag & Drop or "),
                        html.A(
                            "Select CSV/Excel File", href="#", role="button", tabIndex=0
                        ),
                    ],
                    className="upload-instructions",
                ),
                # Restrict to CSV and Excel MIME types
                accept=(
                    ".csv, "
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, "
                    "application/vnd.ms-excel"
                ),
                multiple=False,
                style={
                    "width": "100%",
                    "height": "100px",
                    "lineHeight": "100px",
                    "borderWidth": "2px",
                    "borderStyle": "dashed",
                    "borderRadius": "8px",
                    "textAlign": "center",
                    "backgroundColor": "#f8f9fa",
                    "color": "#495057",
                    "cursor": "pointer",
                    "transition": "background-color 0.2s ease",
                },
                # Change background on hover via CSS class
                className="upload-box",
            ),
            # Feedback area: file name, errors, success messages
            html.Div(id="upload-feedback", className="mt-2 text-secondary"),
        ],
    )

from dash import html


def build_footer():
    """
    Returns a Dash footer component for consistent bottom bar across pages.
    """
    return html.Div(
        children=[
            html.Span("© 2025 AutoClose Inc. "),
            html.Span("Built with "),
            html.Span("♥", style={"color": "red"}),
            html.Span(" for operational excellence"),
            # אפשר להוסיף כאן אייקונים או לינקים בהמשך
        ],
        id="autoclose-footer",
        className="text-center text-muted",
        style={
            "padding": "20px 0",
            "fontSize": "14px",
            "borderTop": "1px solid #eaeaea",
            "marginTop": "60px",
        },
    )

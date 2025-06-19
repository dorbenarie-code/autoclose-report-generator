from dash import html


def build_alert(message: str, category: str = "info"):
    """
    Returns a styled Bootstrap alert box with a close button.

    Parameters
    ----------
    message : str
        The message to be displayed inside the alert.
    category : str
        The Bootstrap color category. Can be one of:
        'success', 'danger', 'warning', 'info', 'primary', 'secondary', etc.
        Defaults to 'info'.

    Returns
    -------
    html.Div
        A Bootstrap alert element with dismissible functionality.
    """
    return html.Div(
        className=f"alert alert-{category} alert-dismissible fade show mt-3",
        role="alert",
        children=[
            # The actual message
            html.Span(message),
            # Close button (Bootstrap 5)
            html.Button(
                className="btn-close",
                **{"data-bs-dismiss": "alert", "aria-label": "Close"},
            ),
        ],
    )

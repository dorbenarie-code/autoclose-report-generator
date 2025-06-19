from dash import html


def build_toast(
    message: str, category: str = "info", delay: int = 3000, rtl: bool = True
) -> html.Div:
    """
    Returns a floating Bootstrap Toast component, with optional RTL support.

    Parameters
    ----------
    message : str
        The message to display in the Toast.
    category : str, optional
        The Bootstrap color category (e.g. 'success', 'danger', 'warning', 'info').
        Default is 'info'.
    delay : int, optional
        Auto-hide delay in milliseconds. Default is 3000 (3 seconds).
    rtl : bool, optional
        If True, positions the toast at the bottom-left (suitable for RTL interfaces).
        Otherwise, positions it at the top-right. Default is True.

    Returns
    -------
    html.Div
        A Bootstrap Toast container with the specified positioning, color, and auto-dismiss.
    """
    # Determine the positioning class based on the rtl flag
    position_class = "bottom-0 start-0" if rtl else "top-0 end-0"

    return html.Div(
        className=f"toast-container position-fixed {position_class} p-3",
        style={"zIndex": 9999},
        children=[
            html.Div(
                className=f"toast align-items-center text-bg-{category} show",
                role="alert",
                data_bs_autohide="true",
                data_bs_delay=str(delay),
                children=[
                    html.Div(
                        className="d-flex",
                        children=[
                            html.Div(className="toast-body", children=message),
                            html.Button(
                                type="button",
                                className="btn-close me-2 m-auto",
                                data_bs_dismiss="toast",
                                aria_label="Close",
                            ),
                        ],
                    )
                ],
            )
        ],
    )

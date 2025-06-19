from dash import html, dcc


def build_email_sender_ui():
    """
    UI block for sending reports by email:
    - Email input field
    - 'Send Now' button
    - Status area (optional)
    """
    return html.Div(
        className="mt-4",
        children=[
            html.H5("📧 Send Report by Email"),
            html.Div(
                className="row g-2",
                children=[
                    html.Div(
                        className="col-md-6",
                        children=[
                            dcc.Input(
                                id="recipient-email",
                                type="email",
                                placeholder="Enter email address...",
                                className="form-control",
                            )
                        ],
                    ),
                    html.Div(
                        className="col-md-4",
                        children=[
                            html.Button(
                                "Send Now",
                                id="send-email-btn",
                                className="btn btn-dark w-100",
                            )
                        ],
                    ),
                ],
            ),
            html.Div(id="send-email-status"),
        ],
    )

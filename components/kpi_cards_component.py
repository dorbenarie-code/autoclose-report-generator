from dash import html


def build_kpi_cards(
    total_reports: int, active_technicians: int, total_amount: float
) -> html.Div:
    """
    Builds 3 KPI cards showing basic summary stats.
    """
    return html.Div(
        className="row g-4 mb-4",
        children=[
            html.Div(
                className="col-md-4",
                children=[
                    html.Div(
                        className="card shadow-sm border-start border-primary border-4",
                        children=[
                            html.Div(
                                className="card-body",
                                children=[
                                    html.H5("📄 Total Reports", className="card-title"),
                                    html.H3(
                                        f"{total_reports}",
                                        className="card-text fw-bold",
                                    ),
                                ],
                            )
                        ],
                    )
                ],
            ),
            html.Div(
                className="col-md-4",
                children=[
                    html.Div(
                        className="card shadow-sm border-start border-success border-4",
                        children=[
                            html.Div(
                                className="card-body",
                                children=[
                                    html.H5(
                                        "👨‍🔧 Active Technicians",
                                        className="card-title",
                                    ),
                                    html.H3(
                                        f"{active_technicians}",
                                        className="card-text fw-bold",
                                    ),
                                ],
                            )
                        ],
                    )
                ],
            ),
            html.Div(
                className="col-md-4",
                children=[
                    html.Div(
                        className="card shadow-sm border-start border-warning border-4",
                        children=[
                            html.Div(
                                className="card-body",
                                children=[
                                    html.H5("💰 Total Amount", className="card-title"),
                                    html.H3(
                                        f"${total_amount:,.2f}",
                                        className="card-text fw-bold",
                                    ),
                                ],
                            )
                        ],
                    )
                ],
            ),
        ],
    )

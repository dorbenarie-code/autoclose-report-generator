from dash import html


def build_exported_reports_list(reports: list):
    """
    Builds a UI component (HTML) that displays a list of exported reports
    with their creation date, filename, and a download button.

    Parameters
    ----------
    reports : list of dict
        List of reports returned by list_exported_reports().
        Each dict must have keys: 'name', 'path', 'created', 'type'.

    Returns
    -------
    html.Div
        A container with a heading and a list of reports or an empty alert if no reports found.
    """
    if not reports:
        return html.Div("📭 No exported reports found.", className="alert alert-info")

    return html.Div(
        [
            html.H5("📂 Exported Reports", className="mb-3"),
            html.Ul(
                children=[
                    html.Li(
                        [
                            html.Span(f"{report['created']} – "),
                            html.Strong(report["name"]),
                            html.A(
                                " Download",
                                href=report["path"],
                                className="btn btn-sm btn-outline-primary ms-2",
                                target="_blank",
                            ),
                        ]
                    )
                    for report in reports
                ],
                className="list-unstyled",
            ),
        ]
    )

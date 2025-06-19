from dash import html
import pandas as pd
import os


def build_email_log_component(log_file: str = "output/sent_email_log.csv"):
    """
    Builds a UI component that displays the email sending history in a table.

    Parameters
    ----------
    log_file : str
        The path to the CSV file containing the email log.
        Defaults to "output/sent_email_log.csv".

    Returns
    -------
    html.Div
        A Dash component containing either an alert if no logs found,
        or a table of the latest 20 log entries, sorted by newest first.
    """
    if not os.path.isfile(log_file):
        return html.Div("📭 No email logs found.", className="alert alert-secondary")

    # Read the CSV log
    # Assuming the CSV columns are: [Time, Recipient, Files, Status, Error]
    df = pd.read_csv(
        log_file, names=["Time", "Recipient", "Files", "Status", "Error"], header=None
    )

    # Show only the latest 20 rows, in reverse order to get newest first
    df = df.tail(20).iloc[::-1]

    # Build table rows
    rows = []
    for _, row in df.iterrows():
        # If Status == "Success", use 'success' color; otherwise 'danger'
        color_class = "success" if row["Status"] == "Success" else "danger"

        rows.append(
            html.Tr(
                [
                    html.Td(row["Time"]),
                    html.Td(row["Recipient"]),
                    html.Td(row["Files"]),
                    html.Td(row["Status"], className=f"text-{color_class}"),
                    html.Td(row["Error"] if pd.notna(row["Error"]) else ""),
                ]
            )
        )

    # Build the final table
    table = html.Table(
        className="table table-striped table-bordered",
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th("Time"),
                        html.Th("Recipient"),
                        html.Th("Files"),
                        html.Th("Status"),
                        html.Th("Error"),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
    )

    return html.Div([html.H5("📬 Email Send History", className="mt-4"), table])

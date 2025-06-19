from dash import html
import os


def build_auto_status(log_path: str = "output/auto_run.log", lines_to_show: int = 10):
    """
    Builds a small UI component that displays the last few lines from an auto-run log file.

    Parameters
    ----------
    log_path : str, optional
        The path to the auto-run log file. Defaults to "output/auto_run.log".
    lines_to_show : int, optional
        The number of lines from the end of the file to display. Defaults to 10.

    Returns
    -------
    html.Div
        A Dash component containing either a message that no log exists,
        or the last 'lines_to_show' lines from the specified log file.
    """
    if not os.path.isfile(log_path):
        return html.Div("🔄 AutoRun has not executed yet.", className="text-muted")

    with open(log_path, "r", encoding="utf-8") as f:
        # Read all lines, then select the last N
        lines = f.readlines()[-lines_to_show:]

    # Build a simple display with a title and a styled <pre> block
    return html.Div(
        [
            html.H5("🕒 AutoRun Log"),
            html.Pre(
                "".join(lines),
                className="bg-light p-3 border",
                style={
                    "whiteSpace": "pre-wrap"
                },  # ensure text wraps nicely if lines are long
            ),
        ]
    )

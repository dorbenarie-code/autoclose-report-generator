# dashboard/callbacks.py

from dash import Input, Output, callback, html, dcc, State, callback_context
import pandas as pd
from plotly.graph_objects import Figure
from myapp.dashboard.graph_utils import create_technician_histogram
from dash import Dash
import plotly.express as px
import logging
import io
from flask import send_file
from dash.exceptions import PreventUpdate
from myapp.services.pdf_export_service import PDFReportExporter
from components.alert_component import build_alert
from components.toast_component import build_toast
from myapp.services.report_list_service import list_exported_reports
from components.exported_reports_component import build_exported_reports_list
from myapp.services.email_service import EmailService
import os
from pathlib import Path

logger = logging.getLogger("AutoCloseDashboard")


def register_callbacks(dash_app: Dash, full_df: pd.DataFrame):
    """
    Register all dashboard callbacks for updating graphs based on user inputs.

    Args:
        dash_app (Dash): The Dash app instance.
        full_df (pd.DataFrame): The full, unfiltered DataFrame loaded from source.
    """

    @dash_app.callback(
        Output("technician-job-type-histogram", "figure"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("job-type-dropdown", "value"),
    )
    def update_histogram(start_date: str, end_date: str, job_type: str) -> Figure:
        """
        Update the histogram figure to show only jobs within the selected date range and job type.

        Args:
            start_date (str): The starting date string in ISO format (YYYY-MM-DD).
            end_date (str): The ending date string in ISO format (YYYY-MM-DD).
            job_type (str): The selected job type from the dropdown.

        Returns:
            Figure: A Plotly Figure for the filtered DataFrame.
        """
        filtered_df = full_df

        # Filter by date
        if start_date and end_date:
            try:
                start = pd.to_datetime(start_date)
                end = pd.to_datetime(end_date)
                if start > end:
                    start, end = end, start
                mask = (filtered_df["date"] >= start) & (filtered_df["date"] <= end)
                filtered_df = filtered_df.loc[mask]
            except Exception:
                pass  # fallback to unfiltered

        # Filter by job_type if selected
        if job_type:
            filtered_df = filtered_df[filtered_df["job_type"] == job_type]

        return create_technician_histogram(filtered_df)

    @callback(
        Output("dashboard-tab-content", "children"), Input("dashboard-tabs", "value")
    )
    def update_tab_content(tab_value):
        """
        Dynamically updates the dashboard-tab-content based on the active tab.
        Tabs:
          - summary: Shows a grouped histogram by technician & job_type
          - by_technician: Shows total reports per technician (bar)
          - by_month: Shows total reports grouped by month (bar)

        Returns: An html.Div containing the relevant graph or error message.
        """
        try:
            df = pd.read_csv("output/merged_jobs.csv")

            # אם הקובץ ריק / אין נתונים
            if df.empty:
                return html.Div("📭 No data available", className="alert alert-info")

            # -- Tab: "summary"
            if tab_value == "summary":
                # Histogram grouped by job_type
                fig = px.histogram(
                    df,
                    x="technician",
                    color="job_type",
                    barmode="group",
                    title="📊 Reports by Technician",
                    labels={
                        "technician": "Technician",
                        "job_type": "Job Type",
                        "count": "Number of Reports",
                    },
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig.update_layout(
                    xaxis_title="Technician",
                    yaxis_title="Count of Reports",
                    legend_title_text="Job Type",
                    template="simple_white",
                )

                return html.Div(
                    [
                        html.H4("📊 General Summary", className="mb-3"),
                        html.Div(
                            dcc.Graph(figure=fig),
                            className="shadow-sm p-3 bg-white rounded",
                        ),
                    ]
                )

            # -- Tab: "by_technician"
            elif tab_value == "by_technician":
                # Group by technician
                df_count = df.groupby("technician").size().reset_index(name="count")
                bar_fig = px.bar(
                    df_count,
                    x="technician",
                    y="count",
                    title="👨‍🔧 Number of Reports by Technician",
                    labels={"technician": "Technician", "count": "Number of Reports"},
                    color="technician",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                bar_fig.update_layout(
                    xaxis_title="Technician",
                    yaxis_title="Count of Reports",
                    showlegend=False,
                    template="simple_white",
                )

                return html.Div(
                    [
                        html.H4("👨‍🔧 Technician Breakdown", className="mb-3"),
                        dcc.Graph(
                            id="technician-bar-graph",
                            figure=bar_fig,
                            clear_on_unhover=True,
                        ),
                        html.Div(id="technician-drilldown"),
                    ]
                )

            # -- Tab: "by_month"
            elif tab_value == "by_month":
                # Convert date to datetime and group by Month
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df["month"] = df["date"].dt.to_period("M").astype(str)
                df_month = df.groupby("month").size().reset_index(name="count")

                fig = px.bar(
                    df_month,
                    x="month",
                    y="count",
                    title="📅 Reports by Month",
                    labels={"month": "Month", "count": "Number of Reports"},
                    color="month",
                    color_discrete_sequence=px.colors.qualitative.Vivid,
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Count of Reports",
                    showlegend=False,
                    template="simple_white",
                )

                return html.Div(
                    [
                        html.H4("📅 Monthly Breakdown", className="mb-3"),
                        dcc.Graph(
                            figure=fig, className="shadow-sm p-3 bg-white rounded"
                        ),
                    ]
                )

            # If tab_value is unknown
            else:
                return html.Div(
                    "Invalid tab selected.", className="alert alert-warning"
                )

        except Exception as e:
            logger.error(f"Error loading data or generating graph: {e}")
            return html.Div(
                f"❌ Error loading data: {e}", className="alert alert-danger"
            )

    @callback(
        Output("main-graph", "figure"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("technician-dropdown", "value"),
        Input("report-type-dropdown", "value"),
    )
    def update_main_graph(start_date, end_date, selected_technician, selected_job_type):
        """
        Updates the main graph based on selected filters:
          - Date range (start_date, end_date)
          - Technician
          - Job Type
        The graph is a histogram grouped by technician, colored by job_type.
        """
        try:
            df = pd.read_csv("output/merged_jobs.csv")

            # Filtering by date range
            if start_date:
                df = df[df["date"] >= start_date]
            if end_date:
                df = df[df["date"] <= end_date]

            # Filtering by technician
            if selected_technician:
                df = df[df["technician"] == selected_technician]

            # Filtering by job_type
            if selected_job_type:
                df = df[df["job_type"] == selected_job_type]

            if df.empty:
                # No data, return empty bar chart
                return px.bar(title="No data found for the selected filters.")

            # Create histogram
            fig = px.histogram(
                df,
                x="technician",
                color="job_type",
                barmode="group",
                title="Reports by Technician",
            )
            fig.update_layout(xaxis_title="Technician", yaxis_title="Count of Reports")

            return fig

        except Exception as e:
            logger.error(f"Failed to update graph: {e}")
            return px.bar(title="Error loading data")

    @callback(
        Output("technician-drilldown", "children"),
        Input("technician-bar-graph", "clickData"),
    )
    def show_technician_details(click_data):
        """
        When a user clicks on a bar in the 'technician-bar-graph',
        this callback will drill down to show a table of all reports for that technician.
        """
        if not click_data:
            return html.Div(
                "Click on a technician bar to see more details.", className="text-muted"
            )

        selected_technician = click_data["points"][0]["x"]

        try:
            df = pd.read_csv("output/merged_jobs.csv")
            df = df[df["technician"] == selected_technician]

            if df.empty:
                return html.Div(
                    f"No reports found for {selected_technician}",
                    className="alert alert-info",
                )

            # נבנה טבלה
            table = html.Table(
                className="table table-striped table-bordered mt-3",
                children=[
                    # כותרת טבלה
                    html.Thead(html.Tr([html.Th(col) for col in df.columns])),
                    # גוף הטבלה (מגבלה של עד 30 שורות)
                    html.Tbody(
                        [
                            html.Tr(
                                [html.Td(str(df.iloc[i][col])) for col in df.columns]
                            )
                            for i in range(min(len(df), 30))
                        ]
                    ),
                ],
            )

            return html.Div(
                [
                    html.H5(
                        f"Reports for Technician: {selected_technician}",
                        className="mt-4",
                    ),
                    table,
                ]
            )

        except Exception as e:
            logger.error(f"[DRILLDOWN ERROR] {e}")
            return html.Div(
                f"❌ Error loading technician details: {e}",
                className="alert alert-danger",
            )

    @callback(
        Output("export-excel-status", "children", allow_duplicate=True),
        Input("export-excel-btn", "n_clicks"),
        Input("export-pdf-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_to_excel(n_clicks, pdf_n_clicks):
        """
        Exports data to an Excel file when the export button is clicked.

        Parameters:
        -----------
        n_clicks : int
            The number of times the "Export to Excel" button has been clicked.
        pdf_n_clicks : int
            The number of times the "Export to PDF" button has been clicked.

        Returns:
        --------
        html.Span or dash.no_update
            A status message (successful or error) to display next to the button.
        """
        # If the button hasn't been clicked, no need to do anything
        if not n_clicks and not pdf_n_clicks:
            raise PreventUpdate

        try:
            # Read the CSV file (later we can filter or transform based on user filters)
            df = pd.read_csv("output/merged_jobs.csv")

            # Prepare file name and path
            filename = "reports_export.xlsx"
            filepath = f"output/{filename}"

            # Export DataFrame to Excel
            df.to_excel(filepath, index=False)

            # Return a success message
            return html.Span(f"✅ Excel exported: {filename}", className="text-success")

        except Exception as e:
            # Log the error for debugging
            logger.error(f"[EXPORT ERROR] {e}")
            # Return an error message
            return html.Span("❌ Failed to export", className="text-danger")

    @callback(
        Output("toast-container", "children", allow_duplicate=True),
        Input("export-pdf-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_pdf(n_clicks):
        """
        Exports a PDF report upon clicking the "Export to PDF" button.
        Displays a toast in RTL position if successful or failed.
        """
        if not n_clicks:
            raise PreventUpdate

        try:
            df = pd.read_csv("output/merged_jobs.csv")
            exporter = PDFReportExporter(df)
            filename = exporter.export()

            return build_toast(
                f"📄 PDF exported successfully: {filename}",
                category="success",
                delay=4000,
                rtl=True,  # Positions at bottom-left
            )

        except Exception as e:
            logger.error(f"[PDF EXPORT ERROR] {e}")
            return build_toast(
                "❌ Failed to export PDF",
                category="danger",
                delay=6000,
                rtl=True,  # Also bottom-left for consistency
            )

    @callback(
        Output("toast-container", "children", allow_duplicate=True),
        Input("send-email-btn", "n_clicks"),
        State("recipient-email", "value"),
        prevent_initial_call=True,
    )
    def handle_send_email(n_clicks, recipient_email):
        """
        Sends the latest report(s) via email to the specified recipient.
        """
        try:
            reports = list_exported_reports()
            latest_pdf = next((r for r in reports if r["type"] == "PDF"), None)
            latest_excel = next((r for r in reports if r["type"] == "Excel"), None)

            if not latest_pdf:
                return build_toast("⚠️ No PDF report available.", category="warning")

            pdf_path = os.path.join("output/reports_exported", latest_pdf["name"])
            attachments = [pdf_path]

            if latest_excel:
                excel_path = os.path.join(
                    "output/reports_exported", latest_excel["name"]
                )
                attachments.append(excel_path)

            start_date = "2025-06-01"
            end_date = "2025-06-30"

            mailer = EmailService()
            mailer.send_monthly_report(
                recipient=recipient_email,
                subject="Monthly Report",
                body="Please find attached the monthly report.",
                pdf_path=Path(pdf_path),
                start_date=str(start_date),
                end_date=str(end_date),
            )

            recipient_str = recipient_email or "default email"
            return build_toast(
                f"✅ Report sent to {recipient_str}", category="success"
            )

        except Exception as e:
            logger.exception(f"Email send failed: {e}")
            return build_toast(
                "❌ Internal error while sending email.", category="danger"
            )

    @callback(
        Output("exported-reports-container", "children"),
        Input("dashboard-tabs", "value"),
    )
    def update_exported_reports(tab_value):
        """
        Dynamically updates the exported reports list,
        showing them only if the user is in the 'summary' tab.
        """
        if tab_value != "summary":
            # Return empty so we don't show the list in other tabs
            return ""

        # Retrieve the list of exported reports (PDF/Excel)
        reports = list_exported_reports()

        # Build and return the UI component
        return build_exported_reports_list(reports)


def register_theme_callback(app: Dash):
    """
    Registers a clientside callback for toggling the theme between dark and light.

    The callback:
    - Listens to the toggle button clicks (theme-toggle).
    - Reads the current stored theme from theme-store.
    - Toggles between 'dark' and 'light'.
    - Updates the HTML tag's data-theme attribute accordingly.
    - Returns the new theme to be stored in theme-store.
    """
    app.clientside_callback(
        """
        function(n, storedTheme) {
            // If storedTheme is 'dark', next is 'light', otherwise 'dark'.
            let nextTheme = (storedTheme === 'dark') ? 'light' : 'dark';
            // Set the data-theme attribute on <html>.
            document.documentElement.setAttribute('data-theme', nextTheme);
            // Return nextTheme so that the Store is updated
            return nextTheme;
        }
        """,
        Output("theme-store", "data"),
        Input("theme-toggle", "n_clicks"),
        Input("theme-store", "data"),
    )

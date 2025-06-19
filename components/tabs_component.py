from dash import dcc


def build_dashboard_tabs():
    """
    Returns the main dashboard Tabs container, with 3 tabs:
      1. Summary
      2. By Technician
      3. By Month
    """
    return dcc.Tabs(
        id="dashboard-tabs",
        value="summary",  # ברירת מחדל היא טאב ה-Summary
        children=[
            dcc.Tab(label="📊 Summary View", value="summary"),
            dcc.Tab(label="👨‍🔧 By Technician", value="by_technician"),
            dcc.Tab(label="📅 By Month", value="by_month"),
        ],
        className="mb-4",
    )

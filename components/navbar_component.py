from dash import html
import dash_bootstrap_components as dbc


def build_navbar():
    """
    Returns a Dash Navbar component for consistent header across Flask and Dash.
    """
    return dbc.NavbarSimple(
        brand="AutoClose Dashboard",
        brand_href="/",
        color="primary",
        dark=True,
        fixed="top",
        children=[
            dbc.NavItem(dbc.NavLink("דף הבית", href="/")),
            dbc.NavItem(dbc.NavLink("דשבורד", href="/dashboard/")),
            dbc.NavItem(dbc.NavLink("חיפוש דוחות", href="/search")),
        ],
        style={"padding": "10px 30px"},
    )

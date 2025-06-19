from dash import html, dcc


def build_theme_toggle():
    """
    Returns a small floating toggle button and a Store component.
    The Store keeps the theme state (light/dark) between sessions using local storage.
    """
    return html.Div(
        children=[
            # Store for theme state, persists across sessions
            dcc.Store(id="theme-store", storage_type="local"),
            # The actual toggle button
            html.Button(
                "🌓",
                id="theme-toggle",
                n_clicks=0,
                className="btn btn-outline-secondary",
                title="Toggle Dark/Light Mode",
            ),
        ],
        style={"position": "fixed", "top": "20px", "left": "20px", "zIndex": 999},
    )

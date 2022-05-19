from dash import Dash, html, dcc
import plotly.express as px
import pandas


def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        server=server,
        routes_pathname_prefix='/dash/',
        external_stylesheets=[
            '/static/dist/css/styles.css',
        ]
    )

    df = pandas.DataFrame({
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples",
                  "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    })

    fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

    # Create Dash Layout
    dash_app.layout = html.Div(children=[
        html.H1(children='Hello Dash'),

        html.Div(children='''
        Dash: A web application framework for your data.
        '''),

        dcc.Graph(
            id='example-graph',
            figure=fig
        )
    ])

    return dash_app.server

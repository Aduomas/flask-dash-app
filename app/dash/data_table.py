import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import dash
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from dash.dependencies import Input, Output
from .dash import Dash

from config import Config
from sqlalchemy import create_engine

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

controls = dbc.Card(
    [
        dbc.Col([]),
    ],
    body=True,
)

app_layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Data Table", style={"textAlign": "center"}),
                    ],
                    md=12,
                )
            ],
            justify="center",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, md=3),
                # dbc.Col(dcc.Graph(id="price-index-graph"), md=8),
            ],
            align="center",
        ),
    ],
    fluid=True,
)


def init_callbacks(dash_app):
    # dash_app.callback()()

    # dash_app.callback()()

    return dash_app


def init_dash(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(server=server, routes_pathname_prefix="/data-table/")

    # create dash layout
    dash_app.layout = app_layout

    # initialize callbacks
    # init_callbacks(dash_app)

    return dash_app.server

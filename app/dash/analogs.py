import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import dash
import pandas as pd
from dash.dependencies import Input, Output, State
from .dash import Dash

from config import Config
from sqlalchemy import create_engine

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)


def get_products():
    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT product.name, product.url, manufacturer.name AS manufacturer, eshop.name AS eshop
            FROM product
            INNER JOIN manufacturer ON product.manufacturer_id = manufacturer.id
            INNER JOIN eshop ON product.eshop_id = eshop.id  
            """,
            conn,
        )
        return df


def update_data_table(value1, value2):
    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT analog.id, p1.name AS product_1, p2.name AS product_2
            FROM analog
            INNER JOIN product AS p1 ON p1.id = analog.product_id_1
            INNER JOIN product AS p2 ON p2.id = analog.product_id_2
            """,
            conn,
        )
        return dbc.Table.from_dataframe(
            df,
            striped=True,
            bordered=True,
            hover=True,
        )


def submit_analog(n_clicks, value_1, value_2):
    if n_clicks is None or n_clicks < 1:
        return dash.no_update

    with engine.begin() as conn:
        conn.execute(
            f"""
            WITH inputvalues(product_id_1, product_id_2) AS (
                VALUES ((SELECT id FROM product WHERE name='{value_1}'), (SELECT id FROM product WHERE name='{value_2}'))
            )
            INSERT INTO analog(product_id_1, product_id_2)
            SELECT d.product_id_1, d.product_id_2
            FROM inputvalues as d
            WHERE d.product_id_1 IS NOT NULL
            AND d.product_id_2 IS NOT NULL;
            """
        )

        print("Uploaded an analog", flush=True)

        return "", "", ""


def remove_analog(n_clicks, value):
    if n_clicks is None or n_clicks < 1:
        return dash.no_update
    with engine.begin() as conn:
        conn.execute(
            f"""
            DELETE
            FROM
            analog
            WHERE analog.id={value}
            """
        )

        print("Removed an analog", flush=True)

        return "", ""


product_names = get_products()["name"].to_list()

controls = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id="analog-dropdown-1",
                            options=[
                                {"label": item, "value": item} for item in product_names
                            ],
                            style={"width": "100%", "color": "black"},
                            optionHeight=55,
                        ),
                    ],
                ),
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id="analog-dropdown-2",
                            options=[
                                {"label": item, "value": item} for item in product_names
                            ],
                            style={
                                "width": "100%",
                                "color": "black",
                            },
                            optionHeight=55,
                        ),
                    ],
                ),
            ]
        ),
    ],
)

app_layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Analogs",
                            style={"textAlign": "center"},
                        ),
                    ],
                    md=12,
                )
            ],
            justify="center",
        ),
        html.Hr(),
        html.P(id="placeholder1"),
        html.P(id="placeholder2"),
        dbc.Row(
            [
                dbc.Col(controls, md=12),
            ],
            align="center",
        ),
        html.Hr(),
        html.Div(
            [
                dbc.Button("Submit analog", id="submit-analog"),
            ],
            className="d-flex justify-content-center",
        ),
        html.Hr(),
        html.Div(
            id="analog-data-table",
            style={
                "width": "50%",
                "margin": "0 auto",
                "maxHeight": "400px",
                "overflow": "scroll",
            },
            children=update_data_table("", ""),
        ),
        html.Hr(),
        html.Div(
            [
                html.P("Type an ID of an analog to remove"),
                dbc.Input(
                    type="number",
                    id="remove-analog-id-value",
                    placeholder="Analog ID",
                ),
            ],
            style={"width": "10%", "margin": "0 auto"},
        ),
        html.Hr(),
        html.Div(
            [
                dbc.Button("Remove analog", id="remove-analog"),
            ],
            className="d-flex justify-content-center",
        ),
    ],
    fluid=True,
)


def init_callbacks(dash_app):

    dash_app.callback(
        Output("analog-data-table", "children"),
        Input("placeholder1", "value"),
        Input("placeholder2", "value"),
    )(update_data_table)

    dash_app.callback(
        Output("analog-dropdown-1", "value"),
        Output("analog-dropdown-2", "value"),
        Output("placeholder1", "value"),
        Input("submit-analog", "n_clicks"),
        State("analog-dropdown-1", "value"),
        State("analog-dropdown-2", "value"),
    )(submit_analog)

    dash_app.callback(
        Output("remove-analog-id-value", "value"),
        Output("placeholder2", "value"),
        Input("remove-analog", "n_clicks"),
        State("remove-analog-id-value", "value"),
    )(remove_analog)

    return dash_app


def init_dash(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(server=server, routes_pathname_prefix="/analogs/")

    # create dash layout
    dash_app.layout = app_layout

    # initialize callbacks
    init_callbacks(dash_app)

    return dash_app.server

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html, dash_table
import pandas as pd
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output
from .dash import Dash

from config import Config
from sqlalchemy import create_engine


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)


def get_products():
    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT DISTINCT ON (product.id) product.name, product.url, manufacturer.name AS manufacturer, eshop.name AS eshop, store.price, date::date
            FROM product
            INNER JOIN manufacturer ON product.manufacturer_id = manufacturer.id
            INNER JOIN eshop ON product.eshop_id = eshop.id
            LEFT JOIN store ON product.id = store.product_id
            ORDER BY product.id, date DESC
            """,
            conn,
        )
        df = df.drop("manufacturer", axis=1)
        df.columns = ["Product Name", "URL", "Eshop", "Last Price", "Date"]
        df = df[["Product Name", "Eshop", "Last Price", "URL", "Date"]]
        return df


product_names = get_products()


controls = dbc.Container(
    [],
)


table = dash_table.DataTable(
    id="analog-data",
    data=product_names.to_dict("records"),
    columns=[{"name": i, "id": i} for i in product_names.columns],
    style_data={
        "color": "black",
        "backgroundColor": "white",
        "height": "auto",
        "whiteSpace": "normal",
    },
    style_table={"height": 800},
    style_data_conditional=[
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "rgb(220, 220, 220)",
        }
    ],
    style_header={
        "backgroundColor": "rgb(210, 210, 210)",
        "color": "black",
        "fontWeight": "bold",
    },
    style_cell_conditional=[
        {"if": {"column_id": c}, "textAlign": "left"} for c in product_names.columns
    ],
    css=[
        {
            "selector": ".Select-menu-outer",
            "rule": "display: block !important",
        }
    ],
    page_size=16,
    filter_action="native",
    sort_action="native",
)

app_layout = dbc.Container(
    [
        html.Hr(),
        html.H2("Product Search", style={"textAlign": "center"}),
        html.Hr(),
        dbc.Card(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [table],
                            md=10,
                        ),
                    ],
                    justify="center",
                ),
            ]
        ),
        html.Hr(),
    ],
    fluid=True,
)


def make_graph_1(manufacturers, eshops, value):
    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT product.id, product.name, store.price, to_char(store.date, 'YYYY-mm-dd') AS date, eshop.name AS e_name, manufacturer.name AS m_name
            FROM store
            INNER JOIN product ON store.product_id=product.id
            INNER JOIN manufacturer ON product.manufacturer_id=manufacturer.id
            INNER JOIN eshop ON product.eshop_id=eshop.id
            WHERE eshop.name IN ({', '.join(f"'{w}'" for w in eshops)})
            AND manufacturer.name IN ({', '.join(f"'{w}'" for w in manufacturers)})
            ORDER BY date ASC;
            """,
            conn,
        )
        df = df.groupby(["date", "m_name"]).price.mean().reset_index()

        fig = px.line(df, x="date", y="price", color="m_name", markers=True, height=600)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(color="#003f5c"),
            xaxis=dict(color="#003f5c"),
            xaxis_title="Date",
            yaxis_title="Price (€)",
            legend_title="Manufacturer",
            font=dict(size=14, color="#7a5195"),
        )
        fig.update_traces(line=dict(width=3))
        fig.update_yaxes(
            title_font_color="#ef5675",
            linecolor="black",
            linewidth=2,
            gridcolor="orange",
        )
        fig.update_xaxes(
            title_font_color="#ef5675",
            linecolor="black",
            linewidth=2,
            gridcolor="#ffa600",
        )

        return fig


def init_callbacks(dash_app):

    # dash_app.callback()()

    return dash_app


def init_dash(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(server=server, routes_pathname_prefix="/data-table/")

    # create dash layout
    dash_app.layout = app_layout

    # initialize callbacks
    init_callbacks(dash_app)

    return dash_app.server

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import pandas as pd
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output
from .dash import Dash

from config import Config
from sqlalchemy import create_engine


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)


def bubble_sort(data, column, ascending):
    n = len(data)
    swapped = False
    for i in range(n - 1):

        for j in range(n - i - 1):

            if ascending:
                if data.loc[j, column] > data.loc[j + 1, column]:
                    swapped = True

                    data.loc[j, :], data.loc[j + 1, :] = (
                        data.loc[j + 1, :],
                        data.loc[j, :],
                    )
            else:
                if data.loc[j, column] < data.loc[j + 1, column]:
                    swapped = True
                    data.loc[j, :], data.loc[j + 1, :] = (
                        data.loc[j + 1, :],
                        data.loc[j, :],
                    )

        if not swapped:
            return


def update_data_table(sort_by_value, sort_order):

    sort_map = {
        "Relative Difference": "percentage_diff",
        "Absolute Difference": "absolute_diff",
        "Price of Product 1": "price1",
        "Price of Product 2": "price2",
        "": "percentage_diff",
    }

    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT DISTINCT ON (s1.date) p1.name AS product_1, s1.price AS price1, p2.name AS product_2, s2.price AS price2, (s1.price / s2.price) AS percentage_diff, (s1.price - s2.price) AS absolute_diff
            FROM analog
            INNER JOIN product AS p1 ON p1.id = analog.product_id_1
            INNER JOIN product AS p2 ON p2.id = analog.product_id_2
            INNER JOIN store AS s1 ON s1.product_id = analog.product_id_1
            INNER JOIN store AS s2 ON s2.product_id = analog.product_id_2
            ORDER BY s1.date DESC
            """,
            conn,
        )
        df["percentage_diff"] = np.round((df["percentage_diff"] - 1) * 100, decimals=2)
        df["percentage_diff"] = df["percentage_diff"].astype(str) + "%"
        df["absolute_diff"] = np.round(df["absolute_diff"], decimals=2)
        # return dbc.Table.from_dataframe(
        #     df.sort_values(
        #         sort_map[sort_by_value],
        #         ascending=True if sort_order == "Ascending" else False,
        #     ),
        #     striped=True,
        #     bordered=True,
        #     hover=True,
        # )
        bubble_sort(
            df, sort_map[sort_by_value], True if sort_order == "Ascending" else False
        )
        return dbc.Table.from_dataframe(
            df,
            striped=True,
            bordered=True,
            hover=True,
        )


controls = dbc.Container(
    [],
)

app_layout = dbc.Container(
    [
        html.Hr(),
        html.H2("Data Table", style={"textAlign": "center"}),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5(
                            "Sort By",
                            style={"textAlign": "center"},
                        ),
                        html.Hr(),
                        dcc.Dropdown(
                            options=[
                                "Relative Difference",
                                "Absolute Difference",
                                "Price of Product 1",
                                "Price of Product 2",
                            ],
                            value="Relative Difference",
                            id="dropdown-sort-1",
                            style={"color": "black"},
                        ),
                        dcc.Dropdown(
                            options=["Ascending", "Descending"],
                            value="Descending",
                            id="dropdown-sort-2",
                            style={"color": "black"},
                        ),
                    ],
                    md=2,
                ),
                dbc.Col(
                    [
                        html.Div(
                            id="analog-data-table-2",
                            style={
                                "width": "80%",
                                "margin": "0 auto",
                                "maxHeight": "400px",
                                "overflow": "scroll",
                            },
                            children=update_data_table(
                                "Relative Difference", "Descending"
                            ),
                        ),
                    ],
                    md=10,
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
    dash_app.callback(
        Output("analog-data-table-2", "children"),
        Input("dropdown-sort-1", "value"),
        Input("dropdown-sort-2", "value"),
    )(update_data_table)

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

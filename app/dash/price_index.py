import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import dash
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
from .dash import Dash

from config import Config
from sqlalchemy import create_engine
from ..crawler.crawler import (
    CrawlerEurovaistine,
    CrawlerBenu,
    CrawlerHerba,
)

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

controls = dbc.Card(
    [
        dbc.Col(
            [
                dbc.Label("Manufacturer Selection", color="#40587e"),
                dbc.Checklist(
                    options=[
                        {"label": item, "value": item}
                        for item in [
                            "Uriage",
                            "Bioderma",
                            "Filorga",
                            "Vichy",
                            "La Roche-Posay",
                            "Svr",
                            "Apivita",
                        ]
                    ],
                    id="checklist-1",
                ),
            ]
        ),
    ],
    body=True,
)


graph_1 = dbc.Col(
    [
        html.Div(
            children=[
                dbc.Select(
                    placeholder="Select an E-shop",
                    options=[
                        {"label": item, "value": item}
                        for item in ["Herba", "Eurovaistine", "Benu", "Gintarine"]
                    ],
                    id="dropdown-1",
                    class_name="mb-2 col-lg-2 offset-lg-4",
                )
            ],
            className="mx-auto",
        ),
        dcc.Graph(id="price-index-graph"),
    ]
)

graph_2 = dbc.Col(
    [
        html.Div(
            children=[
                dbc.Select(
                    placeholder="Select an Manufacturer",
                    options=[
                        {"label": item, "value": item}
                        for item in [
                            "Uriage",
                            "Bioderma",
                            "Filorga",
                            "Vichy",
                            "La Roche-Posay",
                            "Svr",
                            "Apivita",
                        ]
                    ],
                    id="dropdown-2",
                    class_name="mb-2 col-lg-2 offset-lg-4",
                )
            ],
            className="mx-auto",
        ),
        dcc.Graph(id="price-index-graph-2"),
    ]
)


controls2 = dbc.Card(
    [
        dbc.Col(
            [
                dbc.Label("Eshop Selection", color="#40587e"),
                dbc.Checklist(
                    options=[
                        {"label": item, "value": item}
                        for item in ["Herba", "Eurovaistine", "Benu", "Gintarine"]
                    ],
                    id="checklist-2",
                ),
            ]
        ),
    ],
    body=True,
)


app_layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Price Comparison in E-commerce",
                            style={"textAlign": "center"},
                        ),
                    ],
                    md=10,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            id="update-button",
                            children="Update",
                            style={
                                "margin-top": "5px",
                                "height": "80%",
                                "textAlign": "right",
                            },
                        ),
                    ],
                    md=2,
                ),
            ],
            justify="center",
        ),
        html.P(id="placeholder3"),
        html.Hr(),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H3(
                            "Price Comparison based on Eshop",
                            style={"textAlign": "center", "color": "#40587e"},
                        ),
                    ],
                )
            ],
            justify="center",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, md=2),
                dbc.Col(graph_1, md=9),
            ],
            align="center",
        ),
        html.P(id="placeholder4"),
        html.Hr(),
        html.Hr(),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H3(
                            "Price Comparison based on Manufacturer",
                            style={"textAlign": "center", "color": "#40587e"},
                        ),
                    ],
                )
            ],
            justify="center",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls2, md=2),
                dbc.Col(graph_2, md=9),
            ],
            align="center",
        ),
    ],
    fluid=True,
)


def make_graph_1(manufacturers, eshop, value):
    if not (manufacturers and eshop):
        return dash.no_update

    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT product.id, product.name, store.price, to_char(store.date, 'YYYY-mm-dd') AS date, eshop.name AS e_name, manufacturer.name AS m_name
            FROM store
            INNER JOIN product ON store.product_id=product.id
            INNER JOIN manufacturer ON product.manufacturer_id=manufacturer.id
            INNER JOIN eshop ON product.eshop_id=eshop.id
            WHERE eshop.name = '{eshop}'
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


def make_graph_2(eshops, manufacturer, value):
    if not (manufacturer and eshops):
        return dash.no_update

    print(f"{manufacturer=}", flush=True)
    print(f"{eshops=}", flush=True)

    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT product.id, product.name, store.price, to_char(store.date, 'YYYY-mm-dd') AS date, eshop.name AS e_name, manufacturer.name AS m_name
            FROM store
            INNER JOIN product ON store.product_id=product.id
            INNER JOIN manufacturer ON product.manufacturer_id=manufacturer.id
            INNER JOIN eshop ON product.eshop_id=eshop.id
            WHERE eshop.name IN ({', '.join(f"'{w}'" for w in eshops)})
            AND manufacturer.name ='{manufacturer}'
            ORDER BY date ASC;
            """,
            conn,
        )
        df = df.groupby(["date", "e_name"]).price.mean().reset_index()

        fig = px.line(df, x="date", y="price", color="e_name", markers=True, height=600)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(color="#003f5c"),
            xaxis=dict(color="#003f5c"),
            xaxis_title="Date",
            yaxis_title="Price (€)",
            legend_title="Eshop",
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


def update_data(n_clicks):
    if n_clicks is None or n_clicks < 1:
        return dash.no_update

    import sys

    try:
        crawler_eurovaistine = CrawlerEurovaistine()
        crawler_eurovaistine.save(crawler_eurovaistine.crawl())
    except Exception as e:
        print(f"Exception at updating eurovaistine: {e}", file=sys.stderr)

    try:
        crawler_herba = CrawlerHerba()
        crawler_herba.save(crawler_herba.crawl())
    except Exception as e:
        print(f"Exception at updating herba: {e}", file=sys.stderr)

    try:
        crawler_benu = CrawlerBenu()
        crawler_benu.save(crawler_benu.crawl())
    except Exception as e:
        print(f"Exception at updating benu: {e}", file=sys.stderr)

    return [0, 0]


def init_callbacks(dash_app):
    dash_app.callback(
        Output("price-index-graph", "figure"),
        Input("checklist-1", "value"),
        Input("dropdown-1", "value"),
        Input("placeholder3", "value"),
    )(make_graph_1)

    dash_app.callback(
        Output("price-index-graph-2", "figure"),
        Input("checklist-2", "value"),
        Input("dropdown-2", "value"),
        Input("placeholder4", "value"),
    )(make_graph_2)

    dash_app.long_callback(
        inputs=Input("update-button", "n_clicks"),
        running=[(Output("update-button", "disabled"), True, False)],
        output=[Output("placeholder3", "value"), Output("placeholder4", "value")],
        prevent_initial_call=True,
    )(update_data)

    return dash_app


def init_dash(server, meta_viewport, lcm):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        server=server,
        routes_pathname_prefix="/price-index/",
        meta_tags=[meta_viewport],
        long_callback_manager=lcm,
    )

    # create dash layout
    dash_app.layout = app_layout

    # initialize callbacks
    init_callbacks(dash_app)

    return dash_app.server

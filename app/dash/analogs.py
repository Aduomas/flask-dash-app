import dash_bootstrap_components as dbc
from dash import dcc, dash_table
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
        df["name"] = df["eshop"] + " " + df["name"]
        return df


def get_analogs():
    with engine.connect() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT DISTINCT ON(analog.id) analog.id, p1.name AS product_1, store_1.price, p2.name AS product_2, store_2.price, ROUND(CAST(FLOAT8 (store_1.price - store_2.price) AS NUMERIC), 2) AS pdiff, eshop_1.name AS eshop1, eshop_2.name AS eshop2
            FROM analog
            INNER JOIN product AS p1 ON p1.id = analog.product_id_1
            INNER JOIN product AS p2 ON p2.id = analog.product_id_2
            INNER JOIN eshop AS eshop_1 ON p1.eshop_id = eshop_1.id
            INNER JOIN eshop AS eshop_2 ON p2.eshop_id = eshop_2.id
            LEFT JOIN store AS store_1 ON p1.id = store_1.product_id
            LEFT JOIN store AS store_2 ON p2.id = store_2.product_id
			ORDER BY analog.id, store_1.date, store_2.date DESC
            """,
            conn,
        )
        df.columns = [
            "ID",
            "Product Name 1",
            "Last Price 1",
            "Product Name 2",
            "Last Price 2",
            "Price Difference",
            "Eshop 1",
            "Eshop 2",
        ]
        df["Product Name 1"] = df["Eshop 1"] + " " + df["Product Name 1"]
        df["Product Name 2"] = df["Eshop 2"] + " " + df["Product Name 2"]
        df.drop(columns=["Eshop 1", "Eshop 2"], inplace=True)
        print(df.head(), flush=True)
        return df


product_names = get_products()["name"].to_list()
analog_df = get_analogs()


def add_row(n_clicks, rows, columns):
    print(f"{n_clicks=}", flush=True)
    if rows:
        # getting max id from the list of rows
        max_id = max([row["ID"] for row in rows])
    else:
        max_id = 0
    if n_clicks > 0:
        # making a new row
        new_row = {c["id"]: "" for c in columns}
        new_row["ID"] = max_id + 1
        rows.append(new_row)
    # updating current table in the page
    update_analog_data(rows)
    # returning new rows
    return rows


def update_analog_data(data):
    table.data = data


def show_removed_rows(previous, current):
    if previous is None:
        return dash.no_update

    else:
        list_remove_id = [f"{row['ID']}" for row in previous if row not in current]
        list_remove_id = [item for item in list_remove_id if item]

        if list_remove_id:
            with engine.begin() as conn:
                conn.execute(
                    f"""
                DELETE from analog
                WHERE analog.id IN ({",".join(list_remove_id)})
                """
                )
            update_analog_data(current)


def update_analog_table(n_clicks, rows, columns):
    global analog_df
    if n_clicks is None or n_clicks < 1:
        return dash.no_update

    df = pd.DataFrame(rows, columns=[item["name"] for item in columns])

    empty = df[
        (df["Product Name 1"].str.len() == 0) | (df["Product Name 2"].str.len() == 0)
    ]

    print(len(df[~df.index.isin(empty.index.to_list())]), flush=True)
    print(len(df), flush=True)

    with engine.begin() as conn:
        str_list = [
            f"({row['ID']}, (SELECT id FROM product WHERE name='{row['Product Name 1'].split(' ', 1)[1]}'), (SELECT id FROM product WHERE name='{row['Product Name 2'].split(' ', 1)[1]}'))"
            for index, row in df[~df.index.isin(empty.index.to_list())].iterrows()
        ]
        conn.execute(
            f"""
            WITH inputvalues(id, product_id_1, product_id_2) AS (
                VALUES {",".join(str_list)}
            )
            INSERT INTO analog(id, product_id_1, product_id_2)
            SELECT d.id, d.product_id_1, d.product_id_2
            FROM inputvalues as d
            WHERE d.product_id_1 IS NOT NULL
            AND d.product_id_2 IS NOT NULL
            AND d.id IS NOT NULL
            ON CONFLICT (id)
                DO UPDATE SET (product_id_1, product_id_2) = (EXCLUDED.product_id_1, EXCLUDED.product_id_2);
            """
        )

    analog_df = get_analogs()
    print(analog_df.head(), flush=True)
    update_analog_data(analog_df.to_dict("records"))
    return analog_df.to_dict("records")


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

table = dash_table.DataTable(
    id="analog-data",
    data=get_analogs().to_dict("records"),
    columns=[
        {"name": i, "id": i, "presentation": "dropdown"}
        if i != "ID"
        else {"name": i, "id": i, "editable": False}
        for i in analog_df.columns
    ],
    dropdown={
        "Product Name 1": {
            "options": [{"label": i, "value": i} for i in product_names]
        },
        "Product Name 2": {
            "options": [{"label": i, "value": i} for i in product_names]
        },
    },
    editable=True,
    row_deletable=True,
    style_data={
        "color": "black",
        "backgroundColor": "white",
        'whiteSpace': 'normal',
        'height': 'auto',
        'lineHeight': '15px'
    },
    style_table={"height": 400},
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
        {"if": {"column_id": c}, "textAlign": "left"}
        for c in ["Product Name 1", "Product Name 2"]
    ] +
    [{"if": {"column_id": "ID"}, "maxWidth": 30},
     {"if": {"column_id": "Last Price 1"}, "maxWidth": 120},
     {"if": {"column_id": "Last Price 2"}, "maxWidth": 120},
     {"if": {"column_id": "Price Difference"}, "maxWidth": 150},],
    css=[
        {
            "selector": ".Select-menu-outer",
            "rule": "display: block !important",
        }
    ],
    page_size=10,
    filter_action="native",
    sort_action="native",
    fill_width=False,
    # virtualization=True,
)


app_layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Product Comparison Tool",
                            style={"textAlign": "center"},
                        ),
                    ],
                    md=12,
                )
            ],
            justify="center",
        ),
        html.Hr(),
        html.Hr(),
        html.Hr(),
        html.P(id="placeholder5"),
        dbc.Card(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3(
                                    "Equivalent Products",
                                    style={
                                        "textAlign": "center",
                                        "color": "#40587e",
                                        "margin-top": "10px",
                                        "margin-bottom": "10px",
                                    },
                                ),
                            ],
                            md=12,
                        )
                    ],
                    justify="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                table,
                                dcc.Store(id="store-data"),
                                dcc.Store(id="list-remove-id"),
                                dbc.Button(
                                    "Add Row",
                                    id="editing-rows-button",
                                    n_clicks=0,
                                    style={
                                        "margin-top": "5px",
                                        "margin-bottom": "5px",
                                    },
                                ),
                                dbc.Button(
                                    "Save Data",
                                    id="save-data-button",
                                    n_clicks=0,
                                    style={
                                        "margin-top": "5px",
                                        "margin-bottom": "5px",
                                        "margin-left": "40%",
                                    },
                                ),
                            ],
                            md=12,
                        ),
                    ],
                    justify="center",
                ),
            ],
        ),
        html.Hr(),
        html.Hr(),
    ],
    fluid=True,
)


def init_callbacks(dash_app):

    dash_app.callback(
        Output("analog-data", "data"),
        Input("editing-rows-button", "n_clicks"),
        State("analog-data", "data"),
        State("analog-data", "columns"),
    )(add_row)

    dash_app.callback(
        Output("store-data", "data"),
        Input("save-data-button", "n_clicks"),
        State("analog-data", "data"),
        State("analog-data", "columns"),
    )(update_analog_table)
    
    # dash_app.callback(Output("analog-data", "data"),
    #                   Input("store-data", "data"))(update_analog_data)

    dash_app.callback(
        Output("placeholder5", "value"),
        Input("analog-data", "data_previous"),
        State("analog-data", "data"),
    )(show_removed_rows)

    return dash_app


def init_dash(server):
    """Create a Plotly Dash dashboard."""
    # create dash app on /analogs/ endpoint
    dash_app = Dash(
        server=server,
        routes_pathname_prefix="/analogs/",
    )

    # create dash layout
    dash_app.layout = app_layout

    # initialize callbacks
    init_callbacks(dash_app)

    return dash_app.server

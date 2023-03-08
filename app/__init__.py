from flask import Flask
from flask_login import login_required
from dash.long_callback import DiskcacheLongCallbackManager
import diskcache


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.Config")

    register_blueprints(app)
    register_dashapps(app)
    register_extensions(app)

    return app


def register_blueprints(app):
    from .routes import routes
    from .auth import auth

    app.register_blueprint(routes, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")


def register_dashapps(app):
    from .dash import (
        price_index,
        analogs,
        data_table,
    )

    # Meta tags for viewport responsiveness
    meta_viewport = {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1, shrink-to-fit=no",
    }

    cache = diskcache.Cache("./cache")
    lcm = DiskcacheLongCallbackManager(cache)

    with app.app_context():
        app = analogs.init_dash(app)
        app = data_table.init_dash(app)
        app = price_index.init_dash(
            app,
            meta_viewport,
            lcm,
        )
    _protect_dashviews(app)


def _protect_dashviews(dashapp):
    for view_func in dashapp.view_functions:
        if view_func.startswith(
            (
                "/price-index/",
                "/analogs/",
                "/data-table/",
            )
        ):
            dashapp.view_functions[view_func] = login_required(
                dashapp.view_functions[view_func]
            )


def register_extensions(app):
    from app.extensions import db
    from app.extensions import login
    from app.extensions import migrate

    db.init_app(app)
    login.init_app(app)
    login.login_view = "auth.login"
    migrate.init_app(app, db)

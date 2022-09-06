from flask import render_template
from flask import Blueprint
from flask_login import current_user, login_required, login_user, logout_user

routes = Blueprint("routes", __name__)


@routes.route("/")
@login_required
def index():
    return render_template("index.html", content="This is my app!", user=current_user)


@routes.route("/update-data")
@login_required
def update_data():
    pass

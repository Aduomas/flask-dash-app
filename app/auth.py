from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from flask_login import current_user, login_required, login_user, logout_user

auth = Blueprint("auth", __name__)

# login page route
@auth.route("/login", methods=["GET", "POST"])
def login():
    # redirecting to home page if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for("routes.index"))

    # checking whether a request is post, to prevent unwanted requests
    if request.method == "POST":
        # getting data from the form
        username = request.form.get("username")
        password = request.form.get("password")
        remember = request.form.get("remember")
        if remember == "on":
            remember = True
        else:
            remember = False
            
        try:
            user = User.query.filter_by(username=username).first()
        except Exception:
            flash(["Invalid username or password"], category="error")
            return redirect(url_for("auth.login"))
        # checking whether user exists in the database
        if not user:
            flash(["Invalid username or password"], category="error")
            return redirect(url_for("auth.login"))
        # checking whether the password matches with the password in the database
        if check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            # redirecting to the main page if password matches
            return redirect(url_for("routes.index"))
        else:
            # flashing error message and redirecting if password mismatches
            flash(["Invalid username or password"], category="error")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    # checking if user is authenticated
    if current_user.is_authenticated:
        return redirect(url_for("routes.index"))

    if request.method == "POST":
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # checking if the password has proper characters is not too short or too long
        if len(username) < 4:
            flash(["Username must be at least 4 characters long"], category="error")
        elif len(username) >= 15:
            flash(["Username must be at most 15 characters long"], category="error")
        elif password1 != password2:
            flash(["Passwords do not match"], category="error")
        elif len(password1) <= 5:
            flash(["Password must be at least 5 characters long"], category="error")
        elif len(password1) >= 15:
            flash(["Password must be at atmost  15 characters long"], category="error")
        elif not (
            any([x.isupper() for x in password1])
            and any([x.islower() for x in password1])
            and any([x.isdigit() for x in password1])
        ):
            flash(
                [
                    "Password must contain:",
                    "   - at least one capital letter",
                    "   - at least a single number",
                ],
                category="error",
            )
        else:
            # new userr is created and added to database
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password1, method="sha256"),
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("Registration successful", category="success")
            # redirecting to home page
            return redirect(url_for("routes.index"))

    return render_template("register.html")

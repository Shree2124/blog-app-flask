import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__)

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = User.query.filter_by(email=email).first()
        except Exception as e:
            print(f"error : ", e)

        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("view.home"))
            else:
                flash("Password is incorrect", category="error")
        else:
            flash("Email does not exist", category="error")
    return render_template("login.html", user = current_user)


@auth.route("/sign-up", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        try:
            # Validate email format
            if not re.match(EMAIL_REGEX, email):
                flash("Invalid email format.", category="error")

            # Check if email or username already exists
            elif User.query.filter_by(email=email).first():
                flash("Email is already in use.", category="error")
            elif User.query.filter_by(username=username).first():
                flash("Username is already in use.", category="error")

            # Validate other fields
            elif password1 != password2:
                flash("Passwords don't match!", category="error")
            elif len(username) < 2:
                flash("Username is too short.", category="error")
            elif len(password1) < 6:
                flash("Password is too short.", category="error")

            else:
                try:
                
                    new_user = User(
                        email=email,
                        username=username,
                        password=generate_password_hash(password1, method="scrypt"),
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user, remember=True)
                    flash("User created!")
                    return redirect(url_for("view.home"))
                except Exception as e:
                    print("Error: ",e)

        except Exception as e:
            print("Error: ", e)

    return render_template("signup.html", user = current_user)

@auth.route("/logout")
@login_required
def logout():
    logout_user(current_user)
    return redirect(url_for("views.home"))

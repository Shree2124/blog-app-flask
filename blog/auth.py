import re
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    abort,
    session,
    current_app
)
from . import db
from .models import User
import os
import pathlib
import requests
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from dotenv import load_dotenv
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

mail = Mail()
load_dotenv()

auth = Blueprint("auth", __name__)

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
serializer = URLSafeTimedSerializer('helloworld')


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("Missing Google OAuth environment variables")

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
)
flow.redirect_uri = GOOGLE_REDIRECT_URI


@auth.route("/google-login")
def google_login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@auth.route("/auth/google/callback")
def callback():
    try:
        flow.fetch_token(authorization_response=request.url)

        if not session["state"] == request.args["state"]:
            flash("Authorization failed!", category="error")
            return redirect(url_for("auth.login"))

        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID,
        )

        email = id_info.get("email")
        google_id = id_info.get("sub")
        username = id_info.get("name")

        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                new_user = User(
                    email=email, username=username, google_id=google_id, password=None
                )
                db.session.add(new_user)
                db.session.commit()
                user = new_user

            login_user(user)
            flash("Logged in with Google!", category="success")
            return redirect(url_for("view.home"))
        except Exception as e:
            print("Error:", e)
            flash("Error while logging in", category="error")
            return redirect("/home")
        return redirect("/home")
    except Exception as e:
        print("Error ", e)
        flash("some error occurred", category="error")
        return redirect("/home")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = None
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
    return render_template("login.html", user=current_user)


@auth.route("/sign-up", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        try:
            if not re.match(EMAIL_REGEX, email):
                flash("Invalid email format.", category="error")

            elif User.query.filter_by(email=email).first():
                flash("Email is already in use.", category="error")
            elif User.query.filter_by(username=username).first():
                flash("Username is already in use.", category="error")

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
                    print("Error: ", e)

        except Exception as e:
            print("Error: ", e)

    return render_template("signup.html", user=current_user)


@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        try:
            user = User.query.filter_by(email=email).first()
            if user:
                
                token =  serializer.dumps(email, salt="password-reset")
                reset_link = url_for('auth.reset_password', token=token, _external=True)
                
                msg = Message('Password Reset Request', recipients=[email])
                msg.body = f'Click the link to reset your password: {reset_link}'
                mail.send(msg)
                
                flash("Password reset instructions sent to your email.", category="success")
                return redirect(url_for("auth.login"))
            else:
                flash('Email not found.', category='error')
        except Exception as e:
            print("Error ",e)
            flash("Error while sending email", category="error")
    return render_template("forgot_password.html", user=current_user)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try: 
        email= serializer.loads(token, salt='password-reset', max_age=3600)
    except Exception as e:
        flash('The reset link is invalid or expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = generate_password_hash(new_password, method="scrypt")
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.forgot_password'))
    return render_template('reset_password.html', user=current_user)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("view.home"))

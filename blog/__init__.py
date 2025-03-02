from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_mail import Mail
import os

load_dotenv()

db = SQLAlchemy()
DB_NAME = "database.db"


mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "helloworld"

    print(os.getenv("DATABASE_URL"))
    app.config.from_mapping(
        SECRET_KEY="helloworld",
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER"),
    )
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    upload_folder = "blog/static/uploads"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    app.config["UPLOAD_FOLDER"] = upload_folder
    db.init_app(app)
    mail.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models import User, Post, Comments, Like

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists("blog/" + DB_NAME):
        with app.app_context():
            db.create_all()
        print("Created database!")

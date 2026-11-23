from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
oauth = OAuth()

login_manager.login_view = "auth.login"
login_manager.login_message = "Tenés que iniciar sesión para entrar."
login_manager.login_message_category = "error"

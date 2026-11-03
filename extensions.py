
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


# Database extension
db = SQLAlchemy()


# User authentication extension
login_manager = LoginManager()

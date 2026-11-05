
import os
from flask import Flask
from routes.admin.dashboard import admin_bp
from routes.examiner.dashboard import examiner_bp
from routes.student.dashboard import student_bp
from config import Config
from extensions import db, login_manager
from models import User
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.admin.examiner_routes import examiner_admin_bp
@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore[assignment]
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(examiner_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(examiner_admin_bp)
    # Create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

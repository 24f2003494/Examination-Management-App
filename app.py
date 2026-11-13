
import os

from flask import Flask
from config import Config
from extensions import db, login_manager

from models import *
from routes.admin.result_routes import admin_results_bp
# Main routes
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.student.booking_routes import student_booking_bp
# Admin routes
from routes.admin.dashboard import admin_bp
from routes.admin.examiner_routes import examiner_admin_bp
from routes.admin.course_routes import course_admin_bp
from routes.admin.exam_routes import exam_admin_bp
from routes.admin.rubric_routes import rubric_admin_bp
from routes.admin.timeline_routes import timeline_admin_bp
from routes.admin.assignment_routes import assignment_admin_bp
from routes.admin.booking_routes import admin_booking_bp
from routes.admin.search_routes import admin_search_bp
from routes.student.result_routes import student_results_bp
# Examiner routes
from routes.examiner.dashboard import examiner_bp
from routes.examiner.slot_routes import slot_bp
from routes.examiner.participant_routes import participant_bp
from routes.examiner.evaluation_routes import evaluation_bp

# Student routes
from routes.student.dashboard import student_bp

from routes.student.exam_routes import student_exam_bp
from routes.student.booking_routes import student_booking_bp
from routes.student.result_routes import student_results_bp
from routes.student.profile_routes import student_profile_bp

# API routes
from routes.api.examination_api import examination_api
from routes.api.examiner_api import examiner_api
from routes.api.student_api import student_api
from routes.api.slot_api import slot_api
from routes.api.booking_api import booking_api
from routes.api.student_api import student_api
def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore[assignment]

    # Register main blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Register admin blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(examiner_admin_bp)
    app.register_blueprint(course_admin_bp)
    app.register_blueprint(exam_admin_bp)
    app.register_blueprint(rubric_admin_bp)
    app.register_blueprint(timeline_admin_bp)
    app.register_blueprint(assignment_admin_bp)
    app.register_blueprint(admin_booking_bp)
    app.register_blueprint(admin_search_bp)
    app.register_blueprint(admin_results_bp)
    # Register examiner blueprints
    app.register_blueprint(examiner_bp)
    app.register_blueprint(slot_bp)
    app.register_blueprint(participant_bp)
    app.register_blueprint(evaluation_bp)

    # Register student blueprints
    app.register_blueprint(student_bp)
    app.register_blueprint(student_exam_bp)
    app.register_blueprint(student_booking_bp)
    app.register_blueprint(student_results_bp)
    app.register_blueprint(student_profile_bp)
    # Register API blueprints
    app.register_blueprint(examination_api)
    app.register_blueprint(examiner_api)
    app.register_blueprint(student_api)
    app.register_blueprint(slot_api)
    app.register_blueprint(booking_api)
    # Create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return db.session.get(User, int(user_id))


if __name__ == "__main__":
    app.run(debug=True)

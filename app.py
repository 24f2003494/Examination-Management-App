
import os
import secrets
import hmac

from flask import Flask, jsonify, request, session
from config import Config
from extensions import db, login_manager

from models import *
from routes.admin.result_routes import admin_results_bp
             
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
              
from routes.admin.dashboard import admin_bp
from routes.admin.examiner_routes import examiner_admin_bp
from routes.admin.course_routes import course_admin_bp
from routes.admin.exam_routes import exam_admin_bp
from routes.admin.rubric_routes import rubric_admin_bp
from routes.admin.timeline_routes import timeline_admin_bp
from routes.admin.assignment_routes import assignment_admin_bp
from routes.admin.booking_routes import admin_booking_bp
from routes.admin.search_routes import admin_search_bp
                 
from routes.examiner.dashboard import examiner_bp
from routes.examiner.slot_routes import slot_bp
from routes.examiner.participant_routes import participant_bp
from routes.examiner.evaluation_routes import evaluation_bp
from routes.examiner.profile_routes import examiner_profile_bp

                
from routes.student.dashboard import student_bp
from routes.student.exam_routes import student_exam_bp
from routes.student.booking_routes import student_booking_bp
from routes.student.result_routes import student_results_bp
from routes.student.profile_routes import student_profile_bp

            
from routes.api.examination_api import examination_api
from routes.api.examiner_api import examiner_api
from routes.api.student_api import student_api
from routes.api.slot_api import slot_api
from routes.api.booking_api import booking_api
def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"                            
    login_manager.session_protection = "strong"

    @app.context_processor
    def inject_csrf_token():
        def csrf_token():
            token = session.get("_csrf_token")
            if token is None:
                token = secrets.token_urlsafe(32)
                session["_csrf_token"] = token
            return token
        return {"csrf_token": csrf_token}

    @app.before_request
    def protect_form_submissions():
                                                                             
        if (
            request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and not request.path.startswith("/api/")
            and not request.is_json
        ):
            expected = session.get("_csrf_token", "")
            supplied = request.form.get("csrf_token", "")
            if not expected or not supplied or not hmac.compare_digest(expected, supplied):
                return jsonify({"error": "The form session expired. Refresh the page and try again."}), 400

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

                              
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

                               
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
                                  
    app.register_blueprint(examiner_bp)
    app.register_blueprint(slot_bp)
    app.register_blueprint(participant_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(examiner_profile_bp)

                                 
    app.register_blueprint(student_bp)
    app.register_blueprint(student_exam_bp)
    app.register_blueprint(student_booking_bp)
    app.register_blueprint(student_results_bp)
    app.register_blueprint(student_profile_bp)
                             
    app.register_blueprint(examination_api)
    app.register_blueprint(examiner_api)
    app.register_blueprint(student_api)
    app.register_blueprint(slot_api)
    app.register_blueprint(booking_api)
                                                                                    
    with app.app_context():
        db.create_all()

        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        examination_columns = {
            column["name"]
            for column in inspector.get_columns("examinations")
        }

        user_columns = {
            column["name"]
            for column in inspector.get_columns("users")
        }
        if "account_active" not in user_columns:
            with db.engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE users ADD COLUMN account_active BOOLEAN NOT NULL DEFAULT 1"
                ))

        if "status" not in examination_columns:
            with db.engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE examinations "
                    "ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'Draft'"
                ))

                                                                 
        with db.engine.begin() as connection:
            connection.execute(text(
                "UPDATE bookings SET status = 'completed' "
                "WHERE id IN (SELECT booking_id FROM evaluations) "
                "AND lower(status) = 'booked'"
            ))

    return app


app = create_app()


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return db.session.get(User, int(user_id))


if __name__ == "__main__":
    app.run(debug=True)

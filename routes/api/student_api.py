
from flask import Blueprint, jsonify, request
from extensions import db
from models.user import User
from routes.api import role_required

student_api = Blueprint("student_api", __name__, url_prefix="/api/students")


def student_data(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role
    }


@student_api.route("/", methods=["GET"])
@role_required("Admin")
def get_students():
    students = User.query.filter_by(role="Student").all()
    return jsonify([student_data(user) for user in students])


@student_api.route("/<int:user_id>", methods=["GET"])
@role_required("Admin")
def get_student(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != "Student":
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student_data(user))


@student_api.route("/", methods=["POST"])
@role_required("Admin")
def create_student():
    from werkzeug.security import generate_password_hash

    data = request.get_json(silent=True) or {}
    name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Full name, email, and password are required."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered."}), 409

    user = User()
    user.full_name = name
    user.email = email
    user.password_hash = generate_password_hash(password)
    user.role = "Student"
    user.is_approved = True 
    db.session.add(user)
    db.session.commit()
    return jsonify(student_data(user)), 201


@student_api.route("/<int:user_id>", methods=["PUT"])
@role_required("Admin")
def update_student(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != "Student":
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        user.full_name = str(data["full_name"]).strip()

    if "email" in data:
        email = str(data["email"]).strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            return jsonify({"error": "Email is already in use."}), 409
        user.email = email

    db.session.commit()
    return jsonify(student_data(user))


@student_api.route("/<int:user_id>", methods=["DELETE"])
@role_required("Admin")
def deactivate_student(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != "Student":
        return jsonify({"error": "Student not found"}), 404

    # Keep booking and evaluation history; disable login.
    user.is_approved = False
    db.session.commit()
    return jsonify({"message": "Student deactivated successfully."})

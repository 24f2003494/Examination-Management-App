import re

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from extensions import db
from models.user import User
from routes.api import role_required


student_api = Blueprint("student_api", __name__, url_prefix="/api/students")


def student_data(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.account_active
    }


def valid_name_email(name, email):
    return (
        2 <= len(name) <= 100
        and len(email) <= 254
        and bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))
    )


@student_api.route("/", methods=["GET"])
@role_required("admin")
def get_students():
    students = User.query.filter_by(role="student").order_by(User.full_name).all()
    return jsonify([student_data(user) for user in students])


@student_api.route("/<int:user_id>", methods=["GET"])
@role_required("admin")
def get_student(user_id):
    user = User.query.filter_by(id=user_id, role="student").first()
    if not user:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student_data(user))


@student_api.route("/", methods=["POST"])
@role_required("admin")
def create_student():
    data = request.get_json(silent=True) or {}
    name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not valid_name_email(name, email):
        return jsonify({"error": "Provide a valid full name and email."}), 400
    if not isinstance(password, str) or len(password) < 8 or len(password) > 128 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return jsonify({"error": "Password must be 8–128 characters and contain a letter and a number."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered."}), 409

    user = User()
    user.full_name = name
    user.email = email
    user.password_hash = generate_password_hash(password)
    user.role = "student"
    user.is_approved = True
    user.account_active = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to create student."}), 500
    return jsonify(student_data(user)), 201


@student_api.route("/<int:user_id>", methods=["PUT"])
@role_required("admin")
def update_student(user_id):
    user = User.query.filter_by(id=user_id, role="student").first()
    if not user:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json(silent=True) or {}
    if "full_name" in data:
        name = str(data["full_name"]).strip()
        if not 2 <= len(name) <= 100:
            return jsonify({"error": "Full name must contain 2–100 characters."}), 400
        user.full_name = name

    if "email" in data:
        email = str(data["email"]).strip().lower()
        if not valid_name_email(user.full_name, email):
            return jsonify({"error": "Provide a valid email address."}), 400
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            return jsonify({"error": "Email is already in use."}), 409
        user.email = email

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be true or false."}), 400
        user.account_active = data["is_active"]

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to update student."}), 500
    return jsonify(student_data(user))


@student_api.route("/<int:user_id>", methods=["DELETE"])
@role_required("admin")
def deactivate_student(user_id):
    user = User.query.filter_by(id=user_id, role="student").first()
    if not user:
        return jsonify({"error": "Student not found"}), 404

    user.account_active = False
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to deactivate student."}), 500
    return jsonify({"message": "Student deactivated successfully."})


from flask import Blueprint, jsonify, request
from extensions import db
from models.user import User
from routes.api import role_required

examiner_api = Blueprint("examiner_api", __name__, url_prefix="/api/examiners")


def examiner_data(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_approved": user.is_approved
    }


@examiner_api.route("/", methods=["GET"])
@role_required("Admin")
def get_examiners():
    examiners = User.query.filter_by(role="Examiner").all()
    return jsonify([examiner_data(user) for user in examiners])


@examiner_api.route("/<int:user_id>", methods=["GET"])
@role_required("Admin")
def get_examiner(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != "Examiner":
        return jsonify({"error": "Examiner not found"}), 404
    return jsonify(examiner_data(user))


@examiner_api.route("/", methods=["POST"])
@role_required("Admin")
def create_examiner():
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
    return jsonify(examiner_data(user)), 201


@examiner_api.route("/<int:user_id>", methods=["PUT"])
@role_required("Admin")
def update_examiner(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != "Examiner":
        return jsonify({"error": "Examiner not found"}), 404

    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        user.full_name = str(data["full_name"]).strip()

    if "email" in data:
        email = str(data["email"]).strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            return jsonify({"error": "Email is already in use."}), 409
        user.email = email

    if "is_approved" in data:
        user.is_approved = bool(data["is_approved"])

    db.session.commit()
    return jsonify(examiner_data(user))


@examiner_api.route("/<int:user_id>", methods=["DELETE"])
@role_required("Admin")
def deactivate_examiner(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != "Examiner":
        return jsonify({"error": "Examiner not found"}), 404

    # Deactivate without deleting historical records.
    user.is_approved = False
    db.session.commit()
    return jsonify({"message": "Examiner deactivated successfully."})

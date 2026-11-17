
import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models.user import User
from utils.decorators import role_required


student_profile_bp = Blueprint(
    "student_profile",
    __name__,
    url_prefix="/student/profile"
)


@student_profile_bp.route("/", methods=["GET", "POST"])
@role_required("student")
def edit_profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")

        if not full_name or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for("student_profile.edit_profile"))

        if len(full_name) < 2 or len(full_name) > 100:
            flash("Name must contain 2 to 100 characters.", "danger")
            return redirect(url_for("student_profile.edit_profile"))

        if len(email) > 254 or not re.fullmatch(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+", email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("student_profile.edit_profile"))

        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_user:
            flash("This email is already registered.", "danger")
            return redirect(url_for("student_profile.edit_profile"))

        if new_password:
            if not check_password_hash(
                current_user.password_hash,
                current_password
            ):
                flash("Your current password is incorrect.", "danger")
                return redirect(url_for("student_profile.edit_profile"))

            if len(new_password) < 8 or len(new_password) > 128:
                flash("New password must contain 8 to 128 characters.", "danger")
                return redirect(url_for("student_profile.edit_profile"))

            if not re.search(r"[A-Za-z]", new_password) or not re.search(r"[0-9]", new_password):
                flash("New password must contain at least one letter and one number.", "danger")
                return redirect(url_for("student_profile.edit_profile"))

        try:
            current_user.full_name = full_name
            current_user.email = email

            if new_password:
                current_user.password_hash = generate_password_hash(new_password)

            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("student_profile.edit_profile"))

        except Exception:
            db.session.rollback()
            flash("Unable to update your profile.", "danger")

    return render_template("student/profile.html")

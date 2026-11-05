
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from utils.helpers import get_dashboard_url
from extensions import db
from models.user import User
from models.examiner import ExaminerProfile


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(get_dashboard_url(current_user.role))

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip().lower()

        # Validate required fields
        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register"))

        # Validate registration role
        if role not in ["student", "examiner"]:
            flash("Invalid registration role.", "danger")
            return redirect(url_for("auth.register"))

        # Validate password length
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return redirect(url_for("auth.register"))

        # Check whether email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.register"))

        # Create new user
        new_user = User()
        new_user.full_name = full_name
        new_user.email = email
        new_user.password_hash = generate_password_hash(password)
        new_user.role = role
        new_user.is_approved = (role == "student")

        # Create examiner profile when registering as examiner
        if role == "examiner":
            examiner_profile = ExaminerProfile()
            new_user.examiner_profile = examiner_profile

        # Save user and profile to database
        try:
            db.session.add(new_user)
            db.session.commit()

        except Exception:
            db.session.rollback()
            flash("Registration failed. Please try again.", "danger")
            return redirect(url_for("auth.register"))

        # Display registration confirmation
        if role == "examiner":
            flash(
                "Registration successful. Please wait for admin approval.",
                "info"
            )
        else:
            flash(
                "Registration successful. You can now log in.",
                "success"
            )

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(get_dashboard_url(current_user.role))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # Verify user credentials
        if user and check_password_hash(user.password_hash, password):

            # Check examiner approval
            if not user.is_approved:
                flash(
                    "Your account is awaiting admin approval.",
                    "warning"
                )
                return redirect(url_for("auth.login"))

            # Log in approved user
            login_user(user)

            flash("Login successful!", "success")

            return redirect(get_dashboard_url(user.role))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have been logged out.", "info")

    return redirect(url_for("main.home"))

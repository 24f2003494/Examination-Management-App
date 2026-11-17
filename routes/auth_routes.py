
import re

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
        if getattr(current_user, "account_active", True):
            return redirect(get_dashboard_url(current_user.role))
        logout_user()

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip().lower()

                         
        if not full_name or not email or not password or not role:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register"))

                              
        if len(full_name) < 2 or len(full_name) > 100:
            flash("Full name must contain 2 to 100 characters.", "danger")
            return redirect(url_for("auth.register"))

        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", full_name):
            flash("Please enter a valid full name.", "danger")
            return redirect(url_for("auth.register"))

                          
        if len(email) > 254 or not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+", email
        ):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("auth.register"))

                         
        if role not in ["student", "examiner"]:
            flash("Invalid registration role.", "danger")
            return redirect(url_for("auth.register"))

                             
        if len(password) < 8 or len(password) > 128:
            flash("Password must contain 8 to 128 characters.", "danger")
            return redirect(url_for("auth.register"))

        if not re.search(r"[A-Za-z]", password) or not re.search(
            r"[0-9]", password
        ):
            flash(
                "Password must contain at least one letter and one number.",
                "danger"
            )
            return redirect(url_for("auth.register"))

                                    
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.register"))

                     
        new_user = User()
        new_user.full_name = full_name
        new_user.email = email
        new_user.password_hash = generate_password_hash(password)
        new_user.role = role
        new_user.is_approved = (role == "student")

        if role == "examiner":
            new_user.examiner_profile = ExaminerProfile()

        try:
            db.session.add(new_user)
            db.session.commit()

        except Exception:
            db.session.rollback()
            flash("Registration failed. Please try again.", "danger")
            return redirect(url_for("auth.register"))

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

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):

            if not user.account_active:
                flash("Your account has been deactivated. Please contact the administrator.", "danger")
                return redirect(url_for("auth.login"))

            if user.role == "examiner" and not user.is_approved:
                flash(
                    "Your account is awaiting admin approval.",
                    "warning"
                )
                return redirect(url_for("auth.login"))

            login_user(user)

            flash("Login successful!", "success")
            return redirect(get_dashboard_url(user.role))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash("You have been logged out.", "info")

    return redirect(url_for("main.home"))

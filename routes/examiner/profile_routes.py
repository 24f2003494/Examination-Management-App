import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user,login_required

from extensions import db
from models.examiner import ExaminerProfile
from utils.decorators import role_required


examiner_profile_bp = Blueprint(
    "examiner_profile",
    __name__,
    url_prefix="/examiner/profile"
)


@examiner_profile_bp.route("/", methods=["GET", "POST"])
@role_required("examiner")
def edit_profile():
    profile = current_user.examiner_profile
    if profile is None:
        profile = ExaminerProfile()
        profile.user_id=current_user.id
        db.session.add(profile)
        db.session.commit()

    if request.method == "POST":
        qualification = request.form.get("qualification", "").strip()
        specialization = request.form.get("specialization", "").strip()
        experience_value = request.form.get("experience_years", "").strip()

        if len(qualification) > 150 or len(specialization) > 150:
            flash("Qualification and specialization cannot exceed 150 characters.", "danger")
            return redirect(url_for("examiner_profile.edit_profile"))

        try:
            experience = int(experience_value) if experience_value else None
        except ValueError:
            flash("Experience must be a whole number of years.", "danger")
            return redirect(url_for("examiner_profile.edit_profile"))

        if experience is not None and not 0 <= experience <= 60:
            flash("Experience must be between 0 and 60 years.", "danger")
            return redirect(url_for("examiner_profile.edit_profile"))

        profile.qualification = qualification or None
        profile.specialization = specialization or None
        profile.experience_years = experience

        try:
            db.session.commit()
            flash("Examiner profile updated successfully.", "success")
            return redirect(url_for("examiner_profile.edit_profile"))
        except Exception:
            db.session.rollback()
            flash("Unable to update examiner profile.", "danger")

    return render_template("examiner/profile.html", profile=profile)

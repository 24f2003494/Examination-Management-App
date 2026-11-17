import re

from flask import Blueprint, render_template, request, redirect, url_for, flash

from extensions import db
from models.course import Course
from utils.decorators import role_required


course_admin_bp = Blueprint(
    "course_admin",
    __name__,
    url_prefix="/admin/courses"
)


def validate_course(course_name, course_code, description):
    if not course_name or not course_code:
        return "Course name and course code are required."

    if len(course_name) < 2 or len(course_name) > 100:
        return "Course name must be between 2 and 100 characters."

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,19}", course_code):
        return (
            "Course code must be 2–20 characters and contain only "
            "letters, numbers, hyphens or underscores."
        )

    if len(description) > 1000:
        return "Course description cannot exceed 1000 characters."

    return None


@course_admin_bp.route("/")
@role_required("admin")
def course_list():
    courses = Course.query.order_by(Course.course_name).all()

    return render_template(
        "admin/courses.html",
        courses=courses
    )


@course_admin_bp.route("/add", methods=["GET", "POST"])
@role_required("admin")
def add_course():
    if request.method == "POST":
        course_name = request.form.get("course_name", "").strip()
        course_code = request.form.get("course_code", "").strip().upper()
        description = request.form.get("description", "").strip()

        error = validate_course(course_name, course_code, description)

        if error:
            flash(error, "danger")
            return redirect(url_for("course_admin.add_course"))

        existing_course = Course.query.filter(
            (Course.course_name.ilike(course_name)) |
            (Course.course_code == course_code)
        ).first()

        if existing_course:
            flash("Course name or course code already exists.", "danger")
            return redirect(url_for("course_admin.add_course"))

        course = Course()
        course.course_name = course_name
        course.course_code = course_code
        course.description = description or None

        try:
            db.session.add(course)
            db.session.commit()

            flash("Course added successfully!", "success")
            return redirect(url_for("course_admin.course_list"))

        except Exception:
            db.session.rollback()
            flash("Unable to add course. Please try again.", "danger")

    return render_template("admin/add_course.html")


@course_admin_bp.route("/edit/<int:course_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_course(course_id):
    course = db.get_or_404(Course, course_id)

    if request.method == "POST":
        course_name = request.form.get("course_name", "").strip()
        course_code = request.form.get("course_code", "").strip().upper()
        description = request.form.get("description", "").strip()

        error = validate_course(course_name, course_code, description)

        if error:
            flash(error, "danger")
            return redirect(
                url_for("course_admin.edit_course", course_id=course.id)
            )

        duplicate_course = Course.query.filter(
            (
                Course.course_name.ilike(course_name) |
                (Course.course_code == course_code)
            ) &
            (Course.id != course.id)
        ).first()

        if duplicate_course:
            flash("Another course already uses this name or code.", "danger")
            return redirect(
                url_for("course_admin.edit_course", course_id=course.id)
            )

        course.course_name = course_name
        course.course_code = course_code
        course.description = description or None

        try:
            db.session.commit()
            flash("Course updated successfully!", "success")
            return redirect(url_for("course_admin.course_list"))

        except Exception:
            db.session.rollback()
            flash("Unable to update course. Please try again.", "danger")

    return render_template(
        "admin/edit_course.html",
        course=course
    )


@course_admin_bp.route("/delete/<int:course_id>", methods=["POST"])
@role_required("admin")
def delete_course(course_id):
    course = db.get_or_404(Course, course_id)

    if course.examinations:
        flash(
            "This course has associated examinations and cannot be deleted.",
            "warning"
        )
        return redirect(url_for("course_admin.course_list"))

    try:
        db.session.delete(course)
        db.session.commit()
        flash("Course deleted successfully!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to delete course. Please try again.", "danger")

    return redirect(url_for("course_admin.course_list"))
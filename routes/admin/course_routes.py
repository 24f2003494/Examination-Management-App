
from flask import Blueprint, render_template, request, redirect, url_for, flash

from extensions import db
from models.course import Course
from utils.decorators import role_required


course_admin_bp = Blueprint(
    "course_admin",
    __name__,
    url_prefix="/admin/courses"
)


# View all courses
@course_admin_bp.route("/")
@role_required("admin")
def course_list():

    courses = Course.query.order_by(Course.course_name).all()

    return render_template(
        "admin/courses.html",
        courses=courses
    )


# Add a new course
@course_admin_bp.route("/add", methods=["GET", "POST"])
@role_required("admin")
def add_course():

    if request.method == "POST":

        course_name = request.form.get("course_name", "").strip()
        course_code = request.form.get("course_code", "").strip().upper()
        description = request.form.get("description", "").strip()

        if not course_name or not course_code:
            flash("Course name and course code are required.", "danger")
            return redirect(url_for("course_admin.add_course"))

        existing_course = Course.query.filter(
            (Course.course_name == course_name) |
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


# Edit an existing course
@course_admin_bp.route("/edit/<int:course_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_course(course_id):

    course = db.get_or_404(Course, course_id)

    if request.method == "POST":

        course_name = request.form.get("course_name", "").strip()
        course_code = request.form.get("course_code", "").strip().upper()
        description = request.form.get("description", "").strip()

        if not course_name or not course_code:
            flash("Course name and course code are required.", "danger")
            return redirect(
                url_for("course_admin.edit_course", course_id=course.id)
            )

        duplicate_course = Course.query.filter(
            ((Course.course_name == course_name) |
             (Course.course_code == course_code)) &
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


# Delete a course only if it has no examinations
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

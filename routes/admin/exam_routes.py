
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from extensions import db
from models.examination import Examination
from models.course import Course
from utils.decorators import role_required
from models.slot import ExaminationSlot

exam_admin_bp = Blueprint(
    "exam_admin",
    __name__,
    url_prefix="/admin/examinations"
)


# View all examinations
@exam_admin_bp.route("/")
@role_required("admin")
def exam_list():

    examinations = Examination.query.order_by(
        Examination.exam_name
    ).all()

    return render_template(
        "admin/examinations.html",
        examinations=examinations
    )


# Add a new examination
@exam_admin_bp.route("/add", methods=["GET", "POST"])
@role_required("admin")
def add_exam():

    if request.method == "POST":

        exam_name = request.form.get(
            "exam_name", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        course_id = request.form.get(
            "course_id", ""
        ).strip()

        total_marks = request.form.get(
            "total_marks", ""
        ).strip()

        passing_marks = request.form.get(
            "passing_marks", ""
        ).strip()

        if not exam_name or not course_id or not total_marks or not passing_marks:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("exam_admin.add_exam"))

        try:
            course_id = int(course_id)
            total_marks = int(total_marks)
            passing_marks = int(passing_marks)

        except ValueError:
            flash("Please enter valid numeric values.", "danger")
            return redirect(url_for("exam_admin.add_exam"))

        course = db.session.get(Course, course_id)

        if not course:
            flash("Please select a valid course.", "danger")
            return redirect(url_for("exam_admin.add_exam"))

        if total_marks <= 0:
            flash("Total marks must be greater than zero.", "danger")
            return redirect(url_for("exam_admin.add_exam"))

        if passing_marks < 0 or passing_marks > total_marks:
            flash(
                "Passing marks must be between zero and total marks.",
                "danger"
            )
            return redirect(url_for("exam_admin.add_exam"))

        examination = Examination()

        examination.exam_name = exam_name
        examination.description = description or None
        examination.course_id = course_id
        examination.total_marks = total_marks
        examination.passing_marks = passing_marks

        try:
            db.session.add(examination)
            db.session.commit()

            flash("Examination created successfully!", "success")

            return redirect(url_for("exam_admin.exam_list"))

        except Exception:
            db.session.rollback()

            flash(
                "Unable to create examination. Please try again.",
                "danger"
            )

    courses = Course.query.order_by(
        Course.course_name
    ).all()

    return render_template(
        "admin/add_exam.html",
        courses=courses
    )


# Edit an existing examination
@exam_admin_bp.route(
    "/edit/<int:exam_id>",
    methods=["GET", "POST"]
)
@role_required("admin")
def edit_exam(exam_id):

    examination = db.get_or_404(
        Examination,
        exam_id
    )

    if request.method == "POST":

        exam_name = request.form.get(
            "exam_name", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        course_id = request.form.get(
            "course_id", ""
        ).strip()

        total_marks = request.form.get(
            "total_marks", ""
        ).strip()

        passing_marks = request.form.get(
            "passing_marks", ""
        ).strip()

        if not exam_name or not course_id or not total_marks or not passing_marks:
            flash("Please fill in all required fields.", "danger")

            return redirect(
                url_for(
                    "exam_admin.edit_exam",
                    exam_id=exam_id
                )
            )

        try:
            course_id = int(course_id)
            total_marks = int(total_marks)
            passing_marks = int(passing_marks)

        except ValueError:
            flash("Please enter valid numeric values.", "danger")

            return redirect(
                url_for(
                    "exam_admin.edit_exam",
                    exam_id=exam_id
                )
            )

        course = db.session.get(Course, course_id)

        if not course:
            flash("Please select a valid course.", "danger")

            return redirect(
                url_for(
                    "exam_admin.edit_exam",
                    exam_id=exam_id
                )
            )

        if total_marks <= 0:
            flash("Total marks must be greater than zero.", "danger")

            return redirect(
                url_for(
                    "exam_admin.edit_exam",
                    exam_id=exam_id
                )
            )

        if passing_marks < 0 or passing_marks > total_marks:
            flash(
                "Passing marks must be between zero and total marks.",
                "danger"
            )

            return redirect(
                url_for(
                    "exam_admin.edit_exam",
                    exam_id=exam_id
                )
            )

        examination.exam_name = exam_name
        examination.description = description or None
        examination.course_id = course_id
        examination.total_marks = total_marks
        examination.passing_marks = passing_marks

        try:
            db.session.commit()

            flash("Examination updated successfully!", "success")

            return redirect(url_for("exam_admin.exam_list"))

        except Exception:
            db.session.rollback()

            flash(
                "Unable to update examination. Please try again.",
                "danger"
            )

    courses = Course.query.order_by(
        Course.course_name
    ).all()

    return render_template(
        "admin/edit_exam.html",
        examination=examination,
        courses=courses
    )
    # Delete an examination safely
@exam_admin_bp.route(
    "/delete/<int:exam_id>",
    methods=["POST"]
)
@role_required("admin")
def delete_exam(exam_id):

    examination = db.get_or_404(
        Examination,
        exam_id
    )

    # Preserve examination history if slots exist
    existing_slot = ExaminationSlot.query.filter_by(
        examination_id=exam_id
    ).first()

    if existing_slot:
        flash(
            "This examination has associated slots. "
            "It cannot be deleted because historical records must be preserved.",
            "warning"
        )
        return redirect(url_for("exam_admin.exam_list"))
    if examination.rubrics:
        flash(
            "This examination has associated rubrics "
            "and cannot be deleted.",
            "warning"
        )
        return redirect(url_for("exam_admin.exam_list"))
    # Delete only if no slots or associated history exist
    try:
        db.session.delete(examination)
        db.session.commit()

        flash(
            "Examination deleted successfully!",
            "success"
        )

    except Exception:
        db.session.rollback()

        flash(
            "Unable to delete examination. Please try again.",
            "danger"
        )

    return redirect(url_for("exam_admin.exam_list"))
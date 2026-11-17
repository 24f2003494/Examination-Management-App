
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
from models.slot import ExaminationSlot
from utils.decorators import role_required


exam_admin_bp = Blueprint(
    "exam_admin",
    __name__,
    url_prefix="/admin/examinations"
)


                              
EXAMINATION_STATUSES = {
    "Draft", "Slot Creation", "Booking Open", "Closed", "Completed"
}


def validate_exam(exam_name, description, course_id, total_marks, passing_marks, status):

    if not exam_name or not course_id or not total_marks or not passing_marks:
        return "Please fill in all required fields."

    if len(exam_name) < 2 or len(exam_name) > 150:
        return "Examination name must be between 2 and 150 characters."

    if len(description) > 2000:
        return "Examination description cannot exceed 2000 characters."

    if status not in EXAMINATION_STATUSES:
        return "Please select a valid examination status."

    try:
        course_id = int(course_id)
        total_marks = int(total_marks)
        passing_marks = int(passing_marks)

    except ValueError:
        return "Please enter valid numeric values."

    if not db.session.get(Course, course_id):
        return "Please select a valid course."

    if total_marks <= 0 or total_marks > 100000:
        return "Total marks must be between 1 and 100000."

    if passing_marks < 0 or passing_marks > total_marks:
        return "Passing marks must be between zero and total marks."

    return None


                       
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


                       
@exam_admin_bp.route("/add", methods=["GET", "POST"])
@role_required("admin")
def add_exam():

    if request.method == "POST":

        exam_name = request.form.get("exam_name", "").strip()
        description = request.form.get("description", "").strip()
        course_id = request.form.get("course_id", "").strip()
        total_marks = request.form.get("total_marks", "").strip()
        passing_marks = request.form.get("passing_marks", "").strip()
        status = request.form.get("status", "Draft").strip()

        error = validate_exam(
            exam_name,
            description,
            course_id,
            total_marks,
            passing_marks,
            status
        )

        if error:
            flash(error, "danger")
            return redirect(url_for("exam_admin.add_exam"))

                                                  
        examination = Examination()
        examination.exam_name = exam_name
        examination.description = description or None
        examination.course_id = int(course_id)
        examination.total_marks = int(total_marks)
        examination.passing_marks = int(passing_marks)
        examination.status = status

        try:
            db.session.add(examination)
            db.session.commit()

            flash("Examination created successfully!", "success")

            return redirect(url_for("exam_admin.exam_list"))

        except Exception as e:
            db.session.rollback()

            print("EXAMINATION CREATION ERROR:", repr(e))

            flash(
                "Unable to create examination. Please check the terminal.",
                "danger"
            )

    courses = Course.query.order_by(
        Course.course_name
    ).all()

    return render_template(
        "admin/add_exam.html",
        courses=courses
    )


                              
@exam_admin_bp.route("/edit/<int:exam_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_exam(exam_id):

    examination = db.get_or_404(
        Examination,
        exam_id
    )

    if request.method == "POST":

        exam_name = request.form.get("exam_name", "").strip()
        description = request.form.get("description", "").strip()
        course_id = request.form.get("course_id", "").strip()
        total_marks = request.form.get("total_marks", "").strip()
        passing_marks = request.form.get("passing_marks", "").strip()
        status = request.form.get("status", "Draft").strip()

        error = validate_exam(
            exam_name,
            description,
            course_id,
            total_marks,
            passing_marks,
            status
        )

        if error:
            flash(error, "danger")

            return redirect(
                url_for(
                    "exam_admin.edit_exam",
                    exam_id=exam_id
                )
            )

        examination.exam_name = exam_name
        examination.description = description or None
        examination.course_id = int(course_id)
        examination.total_marks = int(total_marks)
        examination.passing_marks = int(passing_marks)
        examination.status = status

        try:
            db.session.commit()

            flash("Examination updated successfully!", "success")

            return redirect(url_for("exam_admin.exam_list"))

        except Exception as e:
            db.session.rollback()

            print("EXAMINATION UPDATE ERROR:", repr(e))

            flash(
                "Unable to update examination. Please check the terminal.",
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

                                  
    if examination.rubrics or examination.examiner_assignments:
        flash(
            "This examination has associated rubrics or examiner assignments and cannot be deleted.",
            "warning"
        )

        return redirect(url_for("exam_admin.exam_list"))

    try:
        db.session.delete(examination)
        db.session.commit()

        flash("Examination deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()

        print("EXAMINATION DELETION ERROR:", repr(e))

        flash(
            "Unable to delete examination. Please check the terminal.",
            "danger"
        )

    return redirect(url_for("exam_admin.exam_list"))

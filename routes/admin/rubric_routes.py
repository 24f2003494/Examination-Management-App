
from flask import Blueprint, render_template, request, redirect, url_for, flash

from extensions import db
from models.examination import Examination
from models.rubric import ExaminationRubric
from utils.decorators import role_required


rubric_admin_bp = Blueprint(
    "rubric_admin",
    __name__,
    url_prefix="/admin/rubrics"
)


# View rubrics for an examination
@rubric_admin_bp.route("/<int:exam_id>")
@role_required("admin")
def rubric_list(exam_id):

    examination = db.session.get(Examination, exam_id)

    if examination is None:
        flash("Examination not found.", "danger")
        return redirect(url_for("exam_admin.exam_list"))

    rubrics = ExaminationRubric.query.filter_by(
        examination_id=exam_id
    ).order_by(ExaminationRubric.id).all()

    return render_template(
        "admin/rubrics.html",
        examination=examination,
        rubrics=rubrics
    )


# Add a rubric
@rubric_admin_bp.route("/<int:exam_id>/add", methods=["GET", "POST"])
@role_required("admin")
def add_rubric(exam_id):

    examination = db.session.get(Examination, exam_id)

    if examination is None:
        flash("Examination not found.", "danger")
        return redirect(url_for("exam_admin.exam_list"))

    if request.method == "POST":

        rubric_name = request.form.get("rubric_name", "").strip()
        description = request.form.get("description", "").strip()
        max_marks_input = request.form.get("max_marks", "").strip()

        if not rubric_name or not max_marks_input:
            flash("Rubric name and maximum marks are required.", "danger")

        else:
            try:
                max_marks = float(max_marks_input)

                if max_marks <= 0:
                    raise ValueError

                rubric = ExaminationRubric()
                rubric.examination_id = exam_id
                rubric.rubric_name = rubric_name
                rubric.description = description
                rubric.max_marks = max_marks

                db.session.add(rubric)
                db.session.commit()

                flash("Rubric added successfully.", "success")

                return redirect(
                    url_for("rubric_admin.rubric_list", exam_id=exam_id)
                )

            except ValueError:
                flash("Maximum marks must be a positive number.", "danger")

    return render_template(
        "admin/add_rubric.html",
        examination=examination
    )


# Edit a rubric
@rubric_admin_bp.route("/edit/<int:rubric_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_rubric(rubric_id):

    rubric = db.session.get(ExaminationRubric, rubric_id)

    if rubric is None:
        flash("Rubric not found.", "danger")
        return redirect(url_for("exam_admin.exam_list"))

    if request.method == "POST":

        rubric_name = request.form.get("rubric_name", "").strip()
        description = request.form.get("description", "").strip()
        max_marks_input = request.form.get("max_marks", "").strip()

        if not rubric_name or not max_marks_input:
            flash("Rubric name and maximum marks are required.", "danger")

        else:
            try:
                max_marks = float(max_marks_input)

                if max_marks <= 0:
                    raise ValueError

                rubric.rubric_name = rubric_name
                rubric.description = description
                rubric.max_marks = max_marks

                db.session.commit()

                flash("Rubric updated successfully.", "success")

                return redirect(
                    url_for(
                        "rubric_admin.rubric_list",
                        exam_id=rubric.examination_id
                    )
                )

            except ValueError:
                flash("Maximum marks must be a positive number.", "danger")

    return render_template(
        "admin/edit_rubric.html",
        rubric=rubric
    )


# Delete a rubric
@rubric_admin_bp.route("/delete/<int:rubric_id>", methods=["POST"])
@role_required("admin")
def delete_rubric(rubric_id):

    rubric = db.session.get(ExaminationRubric, rubric_id)

    if rubric is None:
        flash("Rubric not found.", "danger")
        return redirect(url_for("exam_admin.exam_list"))

    exam_id = rubric.examination_id

    # Do not delete rubrics used in evaluations
    if rubric.rubric_scores:
        flash(
            "This rubric is already used in evaluations and cannot be deleted.",
            "danger"
        )
        return redirect(
            url_for("rubric_admin.rubric_list", exam_id=exam_id)
        )

    db.session.delete(rubric)
    db.session.commit()

    flash("Rubric deleted successfully.", "success")

    return redirect(
        url_for("rubric_admin.rubric_list", exam_id=exam_id)
    )



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

        elif len(rubric_name) > 150:
            flash("Rubric name cannot exceed 150 characters.", "danger")

        elif len(description) > 1000:
            flash("Description cannot exceed 1000 characters.", "danger")

        else:
            try:
                max_marks = float(max_marks_input)

                if max_marks <= 0:
                    raise ValueError

                exam_total_marks = int(examination.total_marks or 0)

                existing_marks = db.session.query(
                    db.func.coalesce(
                        db.func.sum(ExaminationRubric.max_marks), 0
                    )
                ).filter_by(
                    examination_id=exam_id
                ).scalar()

                if float(existing_marks or 0) + max_marks > exam_total_marks:

                    flash(
                        "Total rubric marks cannot exceed examination marks.",
                        "danger"
                    )

                else:
                    rubric = ExaminationRubric()
                    rubric.examination_id = exam_id
                    rubric.rubric_name = rubric_name
                    rubric.description = description or None
                    rubric.max_marks = max_marks

                    db.session.add(rubric)
                    db.session.commit()

                    flash("Rubric added successfully.", "success")

                    return redirect(
                        url_for("rubric_admin.rubric_list", exam_id=exam_id)
                    )

            except ValueError:
                flash(
                    "Maximum marks must be a positive number.",
                    "danger"
                )

            except Exception as e:
                db.session.rollback()
                print("RUBRIC CREATION ERROR:", repr(e))
                flash(
                    "Unable to save rubric. Check the terminal.",
                    "danger"
                )

    return render_template(
        "admin/add_rubric.html",
        examination=examination
    )


               
@rubric_admin_bp.route("/edit/<int:rubric_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_rubric(rubric_id):

    rubric = db.session.get(ExaminationRubric, rubric_id)

    if rubric is None:
        flash("Rubric not found.", "danger")
        return redirect(url_for("exam_admin.exam_list"))

    examination = db.session.get(
        Examination,
        rubric.examination_id
    )

    if examination is None:
        flash("Examination not found.", "danger")
        return redirect(url_for("exam_admin.exam_list"))

    if request.method == "POST":

        rubric_name = request.form.get("rubric_name", "").strip()
        description = request.form.get("description", "").strip()
        max_marks_input = request.form.get("max_marks", "").strip()

        if not rubric_name or not max_marks_input:
            flash("Rubric name and maximum marks are required.", "danger")

        elif len(rubric_name) > 150:
            flash("Rubric name cannot exceed 150 characters.", "danger")

        elif len(description) > 1000:
            flash("Description cannot exceed 1000 characters.", "danger")

        else:
            try:
                max_marks = float(max_marks_input)

                if max_marks <= 0:
                    raise ValueError

                exam_total_marks = int(examination.total_marks or 0)

                existing_marks = db.session.query(
                    db.func.coalesce(
                        db.func.sum(ExaminationRubric.max_marks), 0
                    )
                ).filter(
                    ExaminationRubric.examination_id == rubric.examination_id,
                    ExaminationRubric.id != rubric.id
                ).scalar()

                if float(existing_marks or 0) + max_marks > exam_total_marks:

                    flash(
                        "Total rubric marks cannot exceed examination marks.",
                        "danger"
                    )

                else:
                    rubric.rubric_name = rubric_name
                    rubric.description = description or None
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
                flash(
                    "Maximum marks must be a positive number.",
                    "danger"
                )

            except Exception as e:
                db.session.rollback()
                print("RUBRIC UPDATE ERROR:", repr(e))
                flash(
                    "Unable to update rubric. Check the terminal.",
                    "danger"
                )

    return render_template(
        "admin/edit_rubric.html",
        rubric=rubric,
        examination=examination
    )


                 
@rubric_admin_bp.route("/delete/<int:rubric_id>", methods=["POST"])
@role_required("admin")
def delete_rubric(rubric_id):

    rubric = db.session.get(ExaminationRubric, rubric_id)

    if rubric is None:
        flash("Rubric not found.", "danger")
        return redirect(url_for("exam_admin.exam_list"))

    exam_id = rubric.examination_id

                                                  
    if rubric.rubric_scores:
        flash(
            "This rubric is already used in evaluations and cannot be deleted.",
            "danger"
        )
        return redirect(
            url_for("rubric_admin.rubric_list", exam_id=exam_id)
        )

    try:
        db.session.delete(rubric)
        db.session.commit()

        flash("Rubric deleted successfully.", "success")

    except Exception as e:
        db.session.rollback()
        print("RUBRIC DELETION ERROR:", repr(e))
        flash(
            "Unable to delete rubric. Check the terminal.",
            "danger"
        )

    return redirect(
        url_for("rubric_admin.rubric_list", exam_id=exam_id)
    )

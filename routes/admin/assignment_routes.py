from flask import Blueprint, render_template, request, redirect, url_for, flash

from extensions import db
from models.user import User
from models.examination import Examination
from models.examiner_assignment import ExaminerAssignment
from models.slot import ExaminationSlot
from utils.decorators import role_required


assignment_admin_bp = Blueprint(
    "assignment_admin",
    __name__,
    url_prefix="/admin/assignments"
)


@assignment_admin_bp.route("/")
@role_required("admin")
def assignment_list():

    assignments = ExaminerAssignment.query.order_by(
        ExaminerAssignment.id.desc()
    ).all()

    approved_examiners = User.query.filter_by(
        role="examiner",
        is_approved=True
    ).order_by(User.full_name).all()

    return render_template(
        "admin/assignments.html",
        assignments=assignments,
        approved_examiners=approved_examiners
    )


@assignment_admin_bp.route("/add", methods=["GET", "POST"])
@role_required("admin")
def add_assignment():

    if request.method == "POST":

        examiner_id = request.form.get("examiner_id", type=int)
        examination_id = request.form.get("examination_id", type=int)

        if not examiner_id or not examination_id:
            flash("Please select an examiner and examination.", "danger")
            return redirect(url_for("assignment_admin.add_assignment"))

        examiner = User.query.filter_by(
            id=examiner_id,
            role="examiner",
            is_approved=True
        ).first()

        examination = db.session.get(Examination, examination_id)

        if not examiner:
            flash("Please select a valid approved examiner.", "danger")
            return redirect(url_for("assignment_admin.add_assignment"))

        if not examination:
            flash("Selected examination does not exist.", "danger")
            return redirect(url_for("assignment_admin.add_assignment"))

        existing = ExaminerAssignment.query.filter_by(
            examiner_id=examiner_id,
            examination_id=examination_id
        ).first()

        if existing:
            flash("This examination is already assigned to this examiner.", "warning")
            return redirect(url_for("assignment_admin.add_assignment"))

        assignment = ExaminerAssignment()
        assignment.examiner_id = examiner_id
        assignment.examination_id = examination_id

        try:
            db.session.add(assignment)
            db.session.commit()

            flash("Examination assigned successfully!", "success")
            return redirect(url_for("assignment_admin.assignment_list"))

        except Exception:
            db.session.rollback()
            flash("Unable to assign examination.", "danger")

    examiners = User.query.filter_by(
        role="examiner",
        is_approved=True
    ).order_by(User.full_name).all()

    examinations = Examination.query.order_by(
        Examination.exam_name
    ).all()

    return render_template(
        "admin/add_assignment.html",
        examiners=examiners,
        examinations=examinations
    )

@assignment_admin_bp.route("/change-examiner/<int:assignment_id>", methods=["POST"])
@role_required("admin")
def change_examiner(assignment_id):
    assignment = db.session.get(ExaminerAssignment, assignment_id)
    if assignment is None:
        flash("Examiner assignment not found.", "danger")
        return redirect(url_for("assignment_admin.assignment_list"))

    new_examiner_id = request.form.get("examiner_id", type=int)
    new_examiner = User.query.filter_by(
        id=new_examiner_id,
        role="examiner",
        is_approved=True
    ).first()

    if not new_examiner:
        flash("Please select an approved examiner.", "danger")
        return redirect(url_for("assignment_admin.assignment_list"))

    if new_examiner.id == assignment.examiner_id:
        flash("This examiner is already assigned.", "info")
        return redirect(url_for("assignment_admin.assignment_list"))

    duplicate = ExaminerAssignment.query.filter_by(
        examiner_id=new_examiner.id,
        examination_id=assignment.examination_id
    ).first()
    if duplicate:
        flash("The selected examiner is already assigned to this examination.", "warning")
        return redirect(url_for("assignment_admin.assignment_list"))

                                                                               
                                                                                 
    unbooked_slots = ExaminationSlot.query.filter_by(
        examiner_id=assignment.examiner_id,
        examination_id=assignment.examination_id
    ).filter(~ExaminationSlot.bookings.any()).all()

    for slot in unbooked_slots:
        overlap = ExaminationSlot.query.filter(
            ExaminationSlot.id != slot.id,
            ExaminationSlot.examiner_id == new_examiner.id,
            ExaminationSlot.slot_date == slot.slot_date,
            ExaminationSlot.start_time < slot.end_time,
            ExaminationSlot.end_time > slot.start_time
        ).first()
        if overlap:
            flash(
                "The new examiner has an overlapping slot. Resolve the conflict before reassignment.",
                "danger"
            )
            return redirect(url_for("assignment_admin.assignment_list"))

    try:
        for slot in unbooked_slots:
            slot.examiner_id = new_examiner.id
        assignment.examiner_id = new_examiner.id
        db.session.commit()
        flash(
            "Examiner assignment changed. Existing booked slots retain their original examiner.",
            "success"
        )
    except Exception:
        db.session.rollback()
        flash("Unable to change examiner assignment.", "danger")

    return redirect(url_for("assignment_admin.assignment_list"))

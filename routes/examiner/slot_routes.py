
from datetime import datetime
from services.timeline_service import (
    is_timeline_open,
    has_timeline_started
)
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import current_user

from extensions import db
from models.examiner_assignment import ExaminerAssignment
from models.slot import ExaminationSlot
from models.user import User
from services.slot_service import create_examiner_slot
from utils.decorators import role_required


slot_bp = Blueprint(
    "examiner_slots",
    __name__,
    url_prefix="/examiner/slots"
)


                                                    
                     
                                                    

@slot_bp.route("/")
@role_required("examiner")
def slot_list():

    slots = ExaminationSlot.query.filter_by(
        examiner_id=current_user.id
    ).order_by(
        ExaminationSlot.slot_date,
        ExaminationSlot.start_time
    ).all()

    return render_template(
        "examiner/slots.html",
        slots=slots
    )


                                                    
                         
                                                    

@slot_bp.route("/add", methods=["GET", "POST"])
@role_required("examiner")
def add_slot():

    if not current_user.is_approved:
        flash("Your examiner account is not approved.", "danger")
        return redirect(url_for("examiner.dashboard"))

    assignments = ExaminerAssignment.query.filter_by(
        examiner_id=current_user.id
    ).all()

    examinations = [
        assignment.examination
        for assignment in assignments
    ]

    if request.method == "POST":

        examination_id = request.form.get(
            "examination_id", type=int
        )
        slot_date_value = request.form.get(
            "slot_date", ""
        ).strip()
        start_time_value = request.form.get(
            "start_time", ""
        ).strip()
        end_time_value = request.form.get(
            "end_time", ""
        ).strip()
        capacity = request.form.get(
            "capacity", type=int
        )

        if not all([
            examination_id,
            slot_date_value,
            start_time_value,
            end_time_value,
            capacity
        ]):
            flash("Please complete all fields.", "danger")
            return redirect(url_for("examiner_slots.add_slot"))

        assignment = ExaminerAssignment.query.filter_by(
            examiner_id=current_user.id,
            examination_id=examination_id
        ).first()

        if not assignment:
            flash(
                "You are not assigned to this examination.",
                "danger"
            )
            return redirect(url_for("examiner_slots.add_slot"))

        try:
            slot_date = datetime.strptime(
                slot_date_value, "%Y-%m-%d"
            ).date()

            start_time = datetime.strptime(
                start_time_value, "%H:%M"
            ).time()

            end_time = datetime.strptime(
                end_time_value, "%H:%M"
            ).time()

        except ValueError:
            flash("Please enter valid date and time values.", "danger")
            return redirect(url_for("examiner_slots.add_slot"))

        success, message = create_examiner_slot(
            examination_id=examination_id,
            examiner_id=current_user.id,
            slot_date=slot_date,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity
        )

        if success:
            flash(message, "success")
            return redirect(url_for("examiner_slots.slot_list"))

        flash(message, "danger")

    return render_template(
        "examiner/add_slot.html",
        examinations=examinations
    )


                                                    
                       
                                                    

@slot_bp.route("/edit/<int:slot_id>", methods=["GET", "POST"])
@role_required("examiner")
def edit_slot(slot_id):

    slot = ExaminationSlot.query.filter_by(
        id=slot_id,
        examiner_id=current_user.id
    ).first_or_404()

    if not current_user.is_approved:
        flash("Your examiner account is not approved.", "danger")
        return redirect(url_for("examiner.dashboard"))

    if not is_timeline_open("slot_creation") or has_timeline_started("student_booking"):
        flash(
            "Slot editing is only available during the slot creation period.",
            "warning"
        )
        return redirect(url_for("examiner_slots.slot_list"))

    if slot.bookings:
        flash(
            "Slots with existing bookings cannot be edited.",
            "warning"
        )
        return redirect(url_for("examiner_slots.slot_list"))

    if request.method == "POST":

        slot_date_value = request.form.get(
            "slot_date", ""
        ).strip()
        start_time_value = request.form.get(
            "start_time", ""
        ).strip()
        end_time_value = request.form.get(
            "end_time", ""
        ).strip()
        capacity = request.form.get(
            "capacity", type=int
        )

        try:
            slot_date = datetime.strptime(
                slot_date_value, "%Y-%m-%d"
            ).date()

            start_time = datetime.strptime(
                start_time_value, "%H:%M"
            ).time()

            end_time = datetime.strptime(
                end_time_value, "%H:%M"
            ).time()

        except ValueError:
            flash("Please enter valid date and time values.", "danger")
            return redirect(
                url_for("examiner_slots.edit_slot", slot_id=slot.id)
            )

        if not capacity or capacity <= 0:
            flash("Capacity must be greater than zero.", "danger")
            return redirect(
                url_for("examiner_slots.edit_slot", slot_id=slot.id)
            )

        if slot_date < datetime.today().date():
            flash("You cannot set a slot in the past.", "danger")
            return redirect(
                url_for("examiner_slots.edit_slot", slot_id=slot.id)
            )

        if end_time <= start_time:
            flash("End time must be later than start time.", "danger")
            return redirect(
                url_for("examiner_slots.edit_slot", slot_id=slot.id)
            )

        if slot_date == datetime.today().date() and start_time <= datetime.now().time():
            flash("The slot start time must be in the future.", "danger")
            return redirect(
                url_for("examiner_slots.edit_slot", slot_id=slot.id)
            )

        overlapping_slot = ExaminationSlot.query.filter(
            ExaminationSlot.id != slot.id,
            ExaminationSlot.examiner_id == current_user.id,
            ExaminationSlot.slot_date == slot_date,
            ExaminationSlot.start_time < end_time,
            ExaminationSlot.end_time > start_time
        ).first()

        if overlapping_slot:
            flash("This slot overlaps with another slot.", "danger")
            return redirect(
                url_for("examiner_slots.edit_slot", slot_id=slot.id)
            )

        slot.slot_date = slot_date
        slot.start_time = start_time
        slot.end_time = end_time
        slot.capacity = capacity

        try:
            db.session.commit()
            flash("Slot updated successfully!", "success")
            return redirect(url_for("examiner_slots.slot_list"))

        except Exception:
            db.session.rollback()
            flash("Unable to update slot.", "danger")

    return render_template(
        "examiner/edit_slot.html",
        slot=slot
    )


                                                    
                         
                                                    

@slot_bp.route("/delete/<int:slot_id>", methods=["POST"])
@role_required("examiner")
def delete_slot(slot_id):

    slot = ExaminationSlot.query.filter_by(
        id=slot_id,
        examiner_id=current_user.id
    ).first_or_404()

    if not current_user.is_approved:
        flash("Your examiner account is not approved.", "danger")
        return redirect(url_for("examiner.dashboard"))

    if not is_timeline_open("slot_creation") or has_timeline_started("student_booking"):
        flash("Slot deletion is only available during the slot creation period.", "warning")
        return redirect(url_for("examiner_slots.slot_list"))

    if slot.bookings:
        flash(
            "Slots with existing bookings cannot be deleted.",
            "warning"
        )
        return redirect(url_for("examiner_slots.slot_list"))

    try:
        db.session.delete(slot)
        db.session.commit()

        flash("Slot deleted successfully.", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to delete slot.", "danger")

    return redirect(url_for("examiner_slots.slot_list"))

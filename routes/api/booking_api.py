from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user

from extensions import db
from models.booking import Booking
from models.slot import ExaminationSlot
from models.timeline import SystemTimeline
from routes.api import role_required
from services.booking_service import book_exam_slot


booking_api = Blueprint("booking_api", __name__, url_prefix="/api/bookings")


def booking_data(booking):
    return {
        "id": booking.id,
        "student_id": booking.student_id,
        "student_name": booking.student.full_name,
        "slot_id": booking.slot_id,
        "examination_name": booking.slot.examination.exam_name,
        "slot_date": booking.slot.slot_date.isoformat(),
        "start_time": booking.slot.start_time.strftime("%H:%M"),
        "end_time": booking.slot.end_time.strftime("%H:%M"),
        "status": booking.status,
        "booking_date": booking.booking_date.isoformat()
    }


def refresh_slot_status(slot):
    active_count = Booking.query.filter_by(
        slot_id=slot.id,
        status="booked"
    ).count()
    slot.status = "full" if active_count >= slot.capacity else "available"


@booking_api.route("/", methods=["GET"])
@role_required("admin", "examiner", "student")
def get_bookings():
    query = Booking.query

    if (current_user.role or "").lower() == "student":
        query = query.filter_by(student_id=current_user.id)
    elif (current_user.role or "").lower() == "examiner":
        query = query.join(ExaminationSlot).filter(
            ExaminationSlot.examiner_id == current_user.id
        )

    bookings = query.order_by(Booking.booking_date.desc()).all()
    return jsonify([booking_data(booking) for booking in bookings])


@booking_api.route("/<int:booking_id>", methods=["GET"])
@role_required("admin", "examiner", "student")
def get_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if (current_user.role or "").lower() == "student" and booking.student_id != current_user.id:
        return jsonify({"error": "You cannot view another student's booking."}), 403
    if (current_user.role or "").lower() == "examiner" and booking.slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot view this booking."}), 403

    return jsonify(booking_data(booking))


@booking_api.route("/", methods=["POST"])
@role_required("student")
def create_booking():
    data = request.get_json(silent=True) or {}
    try:
        slot_id = int(data["slot_id"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "A valid slot_id is required."}), 400

    success, message = book_exam_slot(current_user.id, slot_id)
    if not success:
        return jsonify({"error": message}), 400

    booking = Booking.query.filter_by(
        student_id=current_user.id,
        slot_id=slot_id,
        status="booked"
    ).order_by(Booking.id.desc()).first()

    if booking is None:
        return jsonify({"error": "Booking was not saved."}), 500
    return jsonify(booking_data(booking)), 201


@booking_api.route("/<int:booking_id>", methods=["PUT"])
@role_required("admin")
def reschedule_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    if booking.status != "booked":
        return jsonify({"error": "Only active bookings can be rescheduled."}), 409

    data = request.get_json(silent=True) or {}
    try:
        new_slot_id = int(data["slot_id"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "A valid new slot_id is required."}), 400

    new_slot = db.session.get(ExaminationSlot, new_slot_id)
    if not new_slot:
        return jsonify({"error": "New slot not found."}), 404
    old_slot = booking.slot

    if new_slot.id == old_slot.id:
        return jsonify(booking_data(booking))
    if new_slot.examination_id != old_slot.examination_id:
        return jsonify({"error": "The new slot must belong to the same examination."}), 400
    if new_slot.status != "available":
        return jsonify({"error": "The new slot is not available."}), 409
    if not new_slot.examiner or not new_slot.examiner.is_approved or not new_slot.examiner.account_active:
        return jsonify({"error": "The new slot's examiner is not active and approved."}), 409
    if new_slot.slot_date < datetime.now().date() or (
        new_slot.slot_date == datetime.now().date()
        and new_slot.start_time <= datetime.now().time()
    ):
        return jsonify({"error": "The new slot must be in the future."}), 400

    if Booking.query.join(ExaminationSlot).filter(
        Booking.student_id == booking.student_id,
        Booking.status == "booked",
        ExaminationSlot.examination_id == new_slot.examination_id,
        Booking.id != booking.id
    ).first():
        return jsonify({"error": "Student already has an active booking for this examination."}), 409

    active_count = Booking.query.filter_by(
        slot_id=new_slot.id,
        status="booked"
    ).count()
    if active_count >= new_slot.capacity:
        new_slot.status = "full"
        db.session.commit()
        return jsonify({"error": "The new slot is full."}), 409

    booking.slot_id = new_slot.id
    refresh_slot_status(new_slot)
    refresh_slot_status(old_slot)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to reschedule booking."}), 500
    return jsonify(booking_data(booking))


@booking_api.route("/<int:booking_id>", methods=["DELETE"])
@role_required("admin", "student")
def cancel_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    if (current_user.role or "").lower() == "student" and booking.student_id != current_user.id:
        return jsonify({"error": "You cannot cancel another student's booking."}), 403
    if booking.status != "booked":
        return jsonify({"error": "Only active bookings can be cancelled."}), 409

    if (current_user.role or "").lower() == "student":
        timeline = SystemTimeline.query.filter_by(
            setting_name="student_booking",
            is_active=True
        ).first()
        if not timeline or datetime.now() > timeline.end_datetime:
            return jsonify({"error": "The cancellation deadline has passed or booking is closed."}), 400

        slot_start = datetime.combine(
            booking.slot.slot_date,
            booking.slot.start_time
        )
        if datetime.now() >= slot_start:
            return jsonify({"error": "A booking cannot be cancelled after its slot has started."}), 400

    booking.status = "cancelled"
    refresh_slot_status(booking.slot)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to cancel booking."}), 500
    return jsonify({"message": "Booking cancelled successfully."})

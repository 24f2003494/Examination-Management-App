
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import current_user
from extensions import db
from models.booking import Booking
from models.slot import ExaminationSlot
from models.timeline import SystemTimeline
from services.booking_service import book_exam_slot
from routes.api import role_required

booking_api = Blueprint("booking_api", __name__, url_prefix="/api/bookings")


def booking_data(booking):
    return {
        "id": booking.id,
        "student_id": booking.student_id,
        "student_name": booking.student.full_name,
        "slot_id": booking.slot_id,
        "examination_name": booking.slot.examination.exam_name,
        "slot_date": booking.slot.slot_date.isoformat(),
        "status": booking.status,
        "booking_date": booking.booking_date.isoformat()
    }


@booking_api.route("/", methods=["GET"])
@role_required("Admin", "Examiner", "Student")
def get_bookings():
    query = Booking.query

    if current_user.role == "Student":
        query = query.filter_by(student_id=current_user.id)
    elif current_user.role == "Examiner":
        query = query.join(ExaminationSlot).filter(
            ExaminationSlot.examiner_id == current_user.id
        )

    bookings = query.order_by(Booking.booking_date.desc()).all()
    return jsonify([booking_data(booking) for booking in bookings])


@booking_api.route("/<int:booking_id>", methods=["GET"])
@role_required("Admin", "Examiner", "Student")
def get_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if current_user.role == "Student" and booking.student_id != current_user.id:
        return jsonify({"error": "You cannot view another student's booking."}), 403

    if current_user.role == "Examiner" and booking.slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot view this booking."}), 403

    return jsonify(booking_data(booking))


@booking_api.route("/", methods=["POST"])
@role_required("Student")
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
    ).first()

    if not booking:
        return jsonify({"message": message}), 201

    return jsonify(booking_data(booking)), 201


@booking_api.route("/<int:booking_id>", methods=["PUT"])
@role_required("Admin")
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

    if new_slot.examination_id != booking.slot.examination_id:
        return jsonify({"error": "The new slot must belong to the same examination."}), 400

    if new_slot.status != "available":
        return jsonify({"error": "The new slot is not available."}), 409

    if Booking.query.filter_by(
        student_id=booking.student_id,
        slot_id=new_slot_id,
        status="booked"
    ).first():
        return jsonify({"error": "Student already has a booking in this slot."}), 409

    if Booking.query.join(ExaminationSlot).filter(
        Booking.student_id == booking.student_id,
        Booking.status == "booked",
        ExaminationSlot.examination_id == new_slot.examination_id,
        Booking.id != booking.id
    ).first():
        return jsonify({"error": "Student already has an active booking for this examination."}), 409

    active_count = Booking.query.filter_by(
        slot_id=new_slot_id,
        status="booked"
    ).count()

    if active_count >= new_slot.capacity:
        return jsonify({"error": "The new slot is full."}), 409

    old_slot = booking.slot
    booking.slot_id = new_slot.id

    if active_count + 1 >= new_slot.capacity:
        new_slot.status = "full"

    if old_slot.status == "full":
        old_slot.old_slot.status = "available"

    db.session.commit()
    return jsonify(booking_data(booking))


@booking_api.route("/<int:booking_id>", methods=["DELETE"])
@role_required("Admin", "Student")
def cancel_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if current_user.role == "Student" and booking.student_id != current_user.id:
        return jsonify({"error": "You cannot cancel another student's booking."}), 403

    if booking.status != "booked":
        return jsonify({"error": "Only active bookings can be cancelled."}), 409

    timeline = SystemTimeline.query.filter_by(
        setting_name="student_booking",
        is_active=True
    ).first()

    if current_user.role == "Student":
        if not timeline or datetime.now() > timeline.end_datetime:
            return jsonify({"error": "The cancellation deadline has passed or booking is closed."}), 400

    booking.status = "cancelled"

    slot = booking.slot
    active_count = Booking.query.filter_by(
        slot_id=slot.id,
        status="booked"
    ).count()

    if active_count < slot.capacity:
        slot.slot.status = "available"

    db.session.commit()
    return jsonify({"message": "Booking cancelled successfully."})

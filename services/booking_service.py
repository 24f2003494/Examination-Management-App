
from extensions import db
from models.booking import Booking
from models.slot import ExaminationSlot
from services.timeline_service import is_timeline_open


def get_available_slots(examination_id):
    return ExaminationSlot.query.filter_by(
        examination_id=examination_id,
        status="available"
    ).order_by(
        ExaminationSlot.slot_date,
        ExaminationSlot.start_time
    ).all()


def book_exam_slot(student_id, slot_id):
    if not is_timeline_open("student_booking"):
        return False, "Student booking is currently closed."

    slot = db.session.get(ExaminationSlot, slot_id)

    if not slot:
        return False, "The selected slot does not exist."

    if slot.status != "available":
        return False, "This slot is not available."

    if Booking.query.filter_by(
        student_id=student_id,
        slot_id=slot_id,
        status="booked"
    ).first():
        return False, "You have already booked this slot."

    existing_booking = (
        Booking.query
        .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
        .filter(
            Booking.student_id == student_id,
            ExaminationSlot.examination_id == slot.examination_id,
            Booking.status == "booked"
        )
        .first()
    )

    if existing_booking:
        return False, "You have already booked a slot for this examination."

    active_bookings = Booking.query.filter_by(
        slot_id=slot_id,
        status="booked"
    ).count()

    if active_bookings >= slot.capacity:
        slot.status = "full"
        db.session.commit()
        return False, "This slot is already full."

    booking = Booking()
    booking.student_id = student_id
    booking.slot_id = slot_id
    booking.status = "booked"

    try:
        db.session.add(booking)

        if active_bookings + 1 >= slot.capacity:
            slot.status = "full"

        db.session.commit()
        return True, "Slot booked successfully!"

    except Exception:
        db.session.rollback()
        return False, "Unable to complete booking. Please try again."

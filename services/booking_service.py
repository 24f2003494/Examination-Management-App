
from datetime import date, datetime

from extensions import db
from models.booking import Booking
from models.slot import ExaminationSlot
from services.timeline_service import is_timeline_open


def get_available_slots(examination_id):
    if not is_timeline_open("student_booking"):
        return []

    today = date.today()
    now_time = datetime.now().time()
    return ExaminationSlot.query.filter(
        ExaminationSlot.examination_id == examination_id,
        ExaminationSlot.status == "available",
        ExaminationSlot.slot_date >= today
    ).filter(
        (ExaminationSlot.slot_date > today)
        | (ExaminationSlot.start_time > now_time)
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

    if slot.slot_date < date.today():
        return False, "You cannot book a slot in the past."

    if slot.slot_date == date.today() and slot.start_time <= datetime.now().time():
        return False, "The selected slot has already started or passed."

    previous_booking = Booking.query.filter_by(
        student_id=student_id,
        slot_id=slot_id
    ).order_by(Booking.booking_date.desc()).first()

    if previous_booking:
        if previous_booking.status == "booked":
            return False, "You have already booked this slot."
        return False, "This slot was previously cancelled. Please choose another slot."

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
    booking.booking_date = datetime.now()

    try:
        db.session.add(booking)

        if active_bookings + 1 >= slot.capacity:
            slot.status = "full"

        db.session.commit()
        return True, "Slot booked successfully!"

    except Exception:
        db.session.rollback()
        return False, "Unable to complete booking. Please try again."

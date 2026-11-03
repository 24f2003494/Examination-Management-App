
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.booking import Booking
from models.slot import ExaminationSlot


def create_booking(student, slot):

    # Only students can book examination slots
    if student.role != "student":
        return False, "Only students can book examination slots."

    # Check whether the slot is available
    if slot.status != "available":
        return False, "This examination slot is not available."

    # Check whether the student already booked
    # another slot for the same examination
    existing_booking = (
        Booking.query
        .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
        .filter(
            Booking.student_id == student.id,
            Booking.status == "booked",
            ExaminationSlot.examination_id == slot.examination_id
        )
        .first()
    )

    if existing_booking:
        return False, "You have already booked this examination."

    # Count active bookings for this slot
    booked_count = Booking.query.filter_by(
        slot_id=slot.id,
        status="booked"
    ).count()

    if booked_count >= slot.capacity:
        slot.status = "full"
        db.session.commit()
        return False, "This examination slot is full."

    # Create the booking
    new_booking = Booking()

    new_booking.student_id = student.id
    new_booking.slot_id = slot.id
    new_booking.status = "booked"

    try:
        db.session.add(new_booking)

        # Update slot status if capacity is reached
        if booked_count + 1 >= slot.capacity:
            slot.status = "full"

        db.session.commit()

        return True, "Examination slot booked successfully."

    except IntegrityError:
        db.session.rollback()
        return False, "This booking already exists."

    except Exception:
        db.session.rollback()
        raise

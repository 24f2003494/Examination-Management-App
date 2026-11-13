
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user

from extensions import db
from models.examination import Examination
from models.slot import ExaminationSlot
from models.booking import Booking
from models.timeline import SystemTimeline

from services.booking_service import (
    get_available_slots,
    book_exam_slot
)

from utils.decorators import role_required


student_booking_bp = Blueprint(
    "student_bookings",
    __name__,
    url_prefix="/student/bookings"
)


# View available slots for an examination
@student_booking_bp.route("/examination/<int:examination_id>/slots")
@role_required("student")
def slot_list(examination_id):

    examination = db.session.get(Examination, examination_id)

    if examination is None:
        flash("Examination not found.", "danger")
        return redirect(url_for("student_exams.exam_list"))

    slots = get_available_slots(examination_id)

    return render_template(
        "student/available_slots.html",
        examination=examination,
        slots=slots
    )


# Book an examination slot
@student_booking_bp.route("/book/<int:slot_id>", methods=["POST"])
@role_required("student")
def book_slot(slot_id):

    success, message = book_exam_slot(
        current_user.id,
        slot_id
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("student_bookings.booking_list"))


# View all bookings
@student_booking_bp.route("/")
@role_required("student")
def booking_list():

    bookings = Booking.query.filter_by(
        student_id=current_user.id
    ).order_by(
        Booking.booking_date.desc()
    ).all()

    return render_template(
        "student/bookings.html",
        bookings=bookings
    )


# Cancel a booking
@student_booking_bp.route("/cancel/<int:booking_id>", methods=["POST"])
@role_required("student")
def cancel_booking(booking_id):

    booking = db.session.get(Booking, booking_id)

    if booking is None or booking.student_id != current_user.id:
        flash("Booking not found.", "danger")
        return redirect(url_for("student_bookings.booking_list"))

    if booking.status != "booked":
        flash("This booking cannot be cancelled.", "danger")
        return redirect(url_for("student_bookings.booking_list"))

    timeline = SystemTimeline.query.filter_by(
        setting_name="student_booking",
        is_active=True
    ).first()

    if timeline is None or datetime.now() > timeline.end_datetime:
        flash("The booking cancellation deadline has passed.", "danger")
        return redirect(url_for("student_bookings.booking_list"))

    booking.status = "cancelled"

    slot = db.session.get(ExaminationSlot, booking.slot_id)

    if slot:
        active_bookings = Booking.query.filter_by(
            slot_id=slot.id,
            status="booked"
        ).count()

        if active_bookings < slot.capacity:
            slot.status = "available"

    db.session.commit()

    flash("Booking cancelled successfully.", "success")

    return redirect(url_for("student_bookings.booking_list"))


# View upcoming examination schedule
@student_booking_bp.route("/schedule")
@role_required("student")
def schedule():

    bookings = Booking.query.filter_by(
        student_id=current_user.id,
        status="booked"
    ).all()

    upcoming_bookings = [
        booking for booking in bookings
        if booking.slot is not None
        and booking.slot.slot_date >= datetime.now().date()
    ]

    upcoming_bookings.sort(
        key=lambda booking: (
            booking.slot.slot_date,
            booking.slot.start_time
        )
    )

    return render_template(
        "student/schedule.html",
        bookings=upcoming_bookings
    )

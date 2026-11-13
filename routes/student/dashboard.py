
from flask import Blueprint, render_template
from flask_login import current_user

from models.examination import Examination
from models.slot import ExaminationSlot
from models.booking import Booking
from models.evaluation import Evaluation
from services.booking_service import get_available_slots
from utils.decorators import role_required


student_bp = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


@student_bp.route("/dashboard")
@role_required("student")
def dashboard():

    # Count examinations
    total_examinations = Examination.query.count()

    # Count available examination slots
    available_slots = ExaminationSlot.query.filter_by(
        status="available"
    ).count()

    # Get the student's bookings
    student_bookings = Booking.query.filter_by(
        student_id=current_user.id
    ).all()

    total_bookings = len([
        booking for booking in student_bookings
        if booking.status == "booked"
    ])

    # Count upcoming booked examinations
    upcoming_bookings = [
        booking for booking in student_bookings
        if booking.status == "booked"
        and booking.slot is not None
    ]

    # Count published results
    published_results = Evaluation.query.join(
        Booking,
        Evaluation.booking_id == Booking.id
    ).filter(
        Booking.student_id == current_user.id,
        Evaluation.is_published.is_(True)
    ).count()

    counts = {
        "examinations": total_examinations,
        "available_slots": available_slots,
        "upcoming_examinations": len(upcoming_bookings),
        "bookings": total_bookings,
        "published_results": published_results
    }

    return render_template(
        "student/dashboard.html",
        counts=counts
    )

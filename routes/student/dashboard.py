
from datetime import date

from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import func
from datetime import date

from extensions import db
from models.examination import Examination
from models.slot import ExaminationSlot
from models.booking import Booking
from models.evaluation import Evaluation
from utils.decorators import role_required
from services.timeline_service import is_timeline_open


student_bp = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


@student_bp.route("/dashboard")
@role_required("student")
def dashboard():

                                   
    total_examinations = Examination.query.count()

    available_slots = 0
    if is_timeline_open("student_booking"):
        available_slots = ExaminationSlot.query.filter(
            ExaminationSlot.status == "available",
            ExaminationSlot.slot_date >= date.today()
        ).count()

    student_bookings = Booking.query.filter_by(
        student_id=current_user.id
    ).all()

    total_bookings = sum(
        1 for booking in student_bookings
        if booking.status == "booked"
    )

    upcoming_bookings = [
        booking for booking in student_bookings
        if booking.status == "booked"
        and booking.slot is not None
        and booking.slot.slot_date >= date.today()
    ]

    published_results = (
        Evaluation.query
        .join(Booking, Evaluation.booking_id == Booking.id)
        .filter(
            Booking.student_id == current_user.id,
            Evaluation.is_published.is_(True)
        )
        .count()
    )

    counts = {
        "examinations": total_examinations,
        "available_slots": available_slots,
        "upcoming_examinations": len(upcoming_bookings),
        "bookings": total_bookings,
        "published_results": published_results
    }

                                  
    history_data = (
        db.session.query(
            Examination.exam_name,
            func.count(Booking.id)
        )
        .join(
            ExaminationSlot,
            Examination.id == ExaminationSlot.examination_id
        )
        .join(
            Booking,
            ExaminationSlot.id == Booking.slot_id
        )
        .filter(Booking.student_id == current_user.id)
        .group_by(Examination.id, Examination.exam_name)
        .all()
    )

    history_labels = [name for name, total in history_data]
    history_values = [total for name, total in history_data]

                                          
    status_data = (
        db.session.query(
            Booking.status,
            func.count(Booking.id)
        )
        .filter(Booking.student_id == current_user.id)
        .group_by(Booking.status)
        .all()
    )

    status_labels = [
        str(status).capitalize() for status, total in status_data
    ]
    status_values = [total for status, total in status_data]

                                            
    result_data = (
        db.session.query(
            Examination.exam_name,
            Evaluation.marks_obtained
        )
        .join(
            Booking,
            Evaluation.booking_id == Booking.id
        )
        .join(
            ExaminationSlot,
            Booking.slot_id == ExaminationSlot.id
        )
        .join(
            Examination,
            ExaminationSlot.examination_id == Examination.id
        )
        .filter(
            Booking.student_id == current_user.id,
            Evaluation.is_published.is_(True)
        )
        .all()
    )

    result_labels = [name for name, marks in result_data]
    result_values = [float(marks) for name, marks in result_data]

    return render_template(
        "student/dashboard.html",
        counts=counts,
        history_labels=history_labels,
        history_values=history_values,
        status_labels=status_labels,
        status_values=status_values,
        result_labels=result_labels,
        result_values=result_values
    )


from flask import Blueprint, render_template, request
from sqlalchemy import or_

from models.user import User
from models.examination import Examination
from models.booking import Booking
from models.slot import ExaminationSlot
from utils.decorators import role_required


admin_search_bp = Blueprint(
    "admin_search",
    __name__,
    url_prefix="/admin/search"
)


@admin_search_bp.route("/")
@role_required("admin")
def search_records():
    search = request.args.get("q", "").strip()

    students = []
    examiners = []
    examinations = []
    bookings = []

    if search:
        user_filters = [
            User.full_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        ]

        exam_filters = [
            Examination.exam_name.ilike(f"%{search}%")
        ]

        booking_query = (
            Booking.query
            .join(User, Booking.student_id == User.id)
            .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
            .join(Examination, ExaminationSlot.examination_id == Examination.id)
        )

        if search.isdigit():
            user_filters.append(User.id == int(search))
            exam_filters.append(Examination.id == int(search))
            booking_query = booking_query.filter(
                or_(
                    Booking.id == int(search),
                    User.id == int(search)
                )
            )
        else:
            booking_query = booking_query.filter(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    Examination.exam_name.ilike(f"%{search}%")
                )
            )

        students = User.query.filter(
            User.role == "student",
            or_(*user_filters)
        ).all()

        examiners = User.query.filter(
            User.role == "examiner",
            or_(*user_filters)
        ).all()

        examinations = Examination.query.filter(
            or_(*exam_filters)
        ).all()

        bookings = booking_query.order_by(
            Booking.booking_date.desc()
        ).all()

    return render_template(
        "admin/search.html",
        search=search,
        students=students,
        examiners=examiners,
        examinations=examinations,
        bookings=bookings
    )

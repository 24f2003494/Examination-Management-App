
from flask import Blueprint, render_template
from sqlalchemy import func

from models.user import User
from models.course import Course
from models.examination import Examination
from models.slot import ExaminationSlot
from models.booking import Booking
from models.evaluation import Evaluation

from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():

    counts = {
        "courses": Course.query.count(),
        "examinations": Examination.query.count(),
        "examiners": User.query.filter_by(role="examiner").count(),
        "students": User.query.filter_by(role="student").count(),
        "slots": ExaminationSlot.query.count(),
        "bookings": Booking.query.count(),
        "completed_examinations": Examination.query.filter_by(status="Completed").count(),
        "evaluations": Evaluation.query.count()
    }

    examinations = Examination.query.all()

                                          
    booking_status_data = (
        Booking.query.with_entities(
            Booking.status,
            func.count(Booking.id)
        )
        .group_by(Booking.status)
        .all()
    )

    booking_labels = [
        str(status).capitalize() for status, total in booking_status_data
    ]
    booking_values = [total for status, total in booking_status_data]

                                                   
    examiner_data = (
        db_query_examiner_workload()
    )

    examiner_labels = [name for name, total in examiner_data]
    examiner_values = [total for name, total in examiner_data]

                                            
    completion_data = (
        Examination.query.with_entities(
            Examination.status,
            func.count(Examination.id)
        )
        .group_by(Examination.status)
        .all()
    )
    completion_labels = [status for status, total in completion_data]
    completion_values = [total for status, total in completion_data]

                                       
    examination_data = (
        Examination.query
        .outerjoin(ExaminationSlot,
                   Examination.id == ExaminationSlot.examination_id)
        .outerjoin(Booking,
                   ExaminationSlot.id == Booking.slot_id)
        .with_entities(
            Examination.exam_name,
            func.count(Booking.id)
        )
        .group_by(Examination.id, Examination.exam_name)
        .all()
    )

    examination_labels = [name for name, total in examination_data]
    examination_values = [total for name, total in examination_data]

    return render_template(
        "admin/dashboard.html",
        counts=counts,
        examinations=examinations,
        booking_labels=booking_labels,
        booking_values=booking_values,
        examiner_labels=examiner_labels,
        examiner_values=examiner_values,
        examination_labels=examination_labels,
        examination_values=examination_values,
        completion_labels=completion_labels,
        completion_values=completion_values
    )


def db_query_examiner_workload():
    return (
        User.query
        .join(ExaminationSlot, User.id == ExaminationSlot.examiner_id)
        .with_entities(
            User.full_name,
            func.count(ExaminationSlot.id)
        )
        .filter(User.role == "examiner")
        .group_by(User.id, User.full_name)
        .all()
    )

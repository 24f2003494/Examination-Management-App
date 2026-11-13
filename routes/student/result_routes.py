
from flask import Blueprint, render_template
from flask_login import current_user

from models.booking import Booking
from models.evaluation import Evaluation
from utils.decorators import role_required


student_results_bp = Blueprint(
    "student_results",
    __name__,
    url_prefix="/student/results"
)


@student_results_bp.route("/")
@role_required("student")
def result_list():

    evaluations = (
        Evaluation.query
        .join(
            Booking,
            Evaluation.booking_id == Booking.id
        )
        .filter(
            Booking.student_id == current_user.id,
            Evaluation.is_published.is_(True)
        )
        .order_by(Evaluation.evaluated_at.desc())
        .all()
    )

    return render_template(
        "student/results.html",
        evaluations=evaluations
    )

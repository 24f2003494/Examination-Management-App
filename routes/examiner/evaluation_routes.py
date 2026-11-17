
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import current_user

from models.booking import Booking
from models.rubric import ExaminationRubric
from models.evaluation import Evaluation

from services.evaluation_service import (
    submit_evaluation,
    get_pending_evaluations
)

from utils.decorators import role_required


evaluation_bp = Blueprint(
    "examiner_evaluations",
    __name__,
    url_prefix="/examiner/evaluations"
)


@evaluation_bp.route("/")
@role_required("examiner")
def evaluation_list():

    pending_bookings = get_pending_evaluations(current_user.id)

    return render_template(
        "examiner/evaluations.html",
        bookings=pending_bookings
    )


@evaluation_bp.route(
    "/submit/<int:booking_id>",
    methods=["GET", "POST"]
)
@role_required("examiner")
def submit_marks(booking_id):

    booking = Booking.query.filter_by(
        id=booking_id,
        status="booked"
    ).first_or_404()

    if booking.slot.examiner_id != current_user.id:
        flash(
            "You are not authorized to evaluate this student.",
            "danger"
        )
        return redirect(
            url_for("examiner_evaluations.evaluation_list")
        )

                                  
    existing_evaluation = Evaluation.query.filter_by(
        booking_id=booking.id
    ).first()

    if existing_evaluation:
        flash(
            "This student has already been evaluated.",
            "warning"
        )
        return redirect(
            url_for("examiner_evaluations.evaluation_list")
        )

    rubrics = ExaminationRubric.query.filter_by(
        examination_id=booking.slot.examination_id
    ).order_by(ExaminationRubric.id).all()

    entered_marks = {}
    remarks = ""

    if request.method == "POST":

        if not rubrics:
            flash(
                "No evaluation rubrics are configured.",
                "danger"
            )
            return redirect(
                url_for("examiner_evaluations.evaluation_list")
            )

        rubric_marks = {}

        try:
            for rubric in rubrics:

                marks_value = request.form.get(
                    f"rubric_{rubric.id}",
                    ""
                ).strip()

                entered_marks[rubric.id] = marks_value
                rubric_marks[rubric.id] = float(marks_value)

        except (ValueError, TypeError):
            flash(
                "Please enter valid marks for every rubric.",
                "danger"
            )

            return render_template(
                "examiner/submit_evaluation.html",
                booking=booking,
                rubrics=rubrics,
                entered_marks=entered_marks,
                remarks=request.form.get("remarks", "")
            )

        remarks = request.form.get("remarks", "").strip()

        success, message = submit_evaluation(
            booking_id=booking_id,
            examiner_id=current_user.id,
            rubric_marks=rubric_marks,
            remarks=remarks
        )

        if success:
            flash(message, "success")
            return redirect(
                url_for("examiner_evaluations.evaluation_list")
            )

        flash(message, "danger")

    return render_template(
        "examiner/submit_evaluation.html",
        booking=booking,
        rubrics=rubrics,
        entered_marks=entered_marks,
        remarks=remarks
    )

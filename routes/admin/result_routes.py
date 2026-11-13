
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user

from extensions import db
from models.evaluation import Evaluation
from utils.decorators import role_required
from models.booking import Booking

admin_results_bp = Blueprint(
    "admin_results",
    __name__,
    url_prefix="/admin/results"
)



@admin_results_bp.route("/")
@role_required("admin")
def result_list():

    evaluations = (
        Evaluation.query
        .join(
            Booking,
            Evaluation.booking_id == Booking.id
        )
        .order_by(Evaluation.evaluated_at.desc())
        .all()
    )

    return render_template(
        "admin/results.html",
        evaluations=evaluations
    )


@admin_results_bp.route(
    "/publish/<int:evaluation_id>",
    methods=["POST"]
)
@role_required("admin")
def publish_result(evaluation_id):

    evaluation = db.session.get(Evaluation, evaluation_id)

    if evaluation is None:
        flash("Evaluation not found.", "danger")
        return redirect(url_for("admin_results.result_list"))

    if evaluation.is_published:
        flash("This result has already been published.", "info")
        return redirect(url_for("admin_results.result_list"))

    try:
        evaluation.is_published = True
        db.session.commit()

        flash(
            "Examination result published successfully.",
            "success"
        )

    except Exception:
        db.session.rollback()
        flash("Unable to publish the result.", "danger")

    return redirect(url_for("admin_results.result_list"))

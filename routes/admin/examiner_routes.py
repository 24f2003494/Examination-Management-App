
from flask import Blueprint, render_template, redirect, url_for, flash
from utils.decorators import role_required
from extensions import db
from models.user import User


examiner_admin_bp = Blueprint(
    "examiner_admin",
    __name__,
    url_prefix="/admin/examiners"
)


@examiner_admin_bp.route("/")
@role_required("admin")
def examiner_list():

    pending_examiners = User.query.filter_by(
        role="examiner",
        is_approved=False
    ).all()

    approved_examiners = User.query.filter_by(
        role="examiner",
        is_approved=True
    ).all()

    return render_template(
        "admin/examiners.html",
        pending_examiners=pending_examiners,
        approved_examiners=approved_examiners
    )


@examiner_admin_bp.route("/approve/<int:user_id>", methods=["POST"])
@role_required("admin")
def approve_examiner(user_id):

    examiner = User.query.filter_by(
        id=user_id,
        role="examiner"
    ).first_or_404()

    examiner.is_approved = True

    db.session.commit()

    flash(
        f"{examiner.full_name} has been approved successfully.",
        "success"
    )

    return redirect(url_for("examiner_admin.examiner_list"))

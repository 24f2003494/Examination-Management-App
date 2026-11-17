
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
        role="examiner", is_approved=False, account_active=True
    ).all()

    approved_examiners = User.query.filter_by(
        role="examiner", is_approved=True, account_active=True
    ).all()

    deactivated_examiners = User.query.filter_by(
        role="examiner", account_active=False
    ).all()

    return render_template(
        "admin/examiners.html",
        pending_examiners=pending_examiners,
        approved_examiners=approved_examiners,
        deactivated_examiners=deactivated_examiners
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


@examiner_admin_bp.route("/deactivate/<int:user_id>", methods=["POST"])
@role_required("admin")
def deactivate_examiner(user_id):
    examiner = User.query.filter_by(
        id=user_id,
        role="examiner"
    ).first_or_404()

    examiner.account_active = False

    try:
        db.session.commit()
        flash(
            f"{examiner.full_name}'s examiner access has been deactivated.",
            "success"
        )
    except Exception:
        db.session.rollback()
        flash("Unable to deactivate this examiner.", "danger")

    return redirect(url_for("examiner_admin.examiner_list"))


@examiner_admin_bp.route("/reactivate/<int:user_id>", methods=["POST"])
@role_required("admin")
def reactivate_examiner(user_id):
    examiner = User.query.filter_by(
        id=user_id, role="examiner"
    ).first_or_404()
    examiner.account_active = True
    try:
        db.session.commit()
        flash(f"{examiner.full_name}'s account has been reactivated.", "success")
    except Exception:
        db.session.rollback()
        flash("Unable to reactivate this examiner.", "danger")
    return redirect(url_for("examiner_admin.examiner_list"))

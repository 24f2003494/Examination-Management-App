
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from extensions import db
from models.timeline import SystemTimeline
from utils.decorators import role_required


timeline_admin_bp = Blueprint(
    "timeline_admin",
    __name__,
    url_prefix="/admin/timelines"
)


ALLOWED_TIMELINES = {
    "slot_creation",
    "student_booking"
}


                       
@timeline_admin_bp.route("/")
@role_required("admin")
def timeline_list():

    timelines = SystemTimeline.query.order_by(
        SystemTimeline.id
    ).all()

    return render_template(
        "admin/timelines.html",
        timelines=timelines
    )


                
@timeline_admin_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@role_required("admin")
def add_timeline():

    if request.method == "POST":

        setting_name = request.form.get(
            "setting_name", ""
        ).strip()

        start_datetime = request.form.get(
            "start_datetime", ""
        ).strip()

        end_datetime = request.form.get(
            "end_datetime", ""
        ).strip()

        if setting_name not in ALLOWED_TIMELINES:
            flash(
                "Please select a valid timeline type.",
                "danger"
            )
            return redirect(
                url_for("timeline_admin.add_timeline")
            )

        if not start_datetime or not end_datetime:
            flash(
                "Please fill in all required fields.",
                "danger"
            )
            return redirect(
                url_for("timeline_admin.add_timeline")
            )

        try:
            start = datetime.fromisoformat(start_datetime)
            end = datetime.fromisoformat(end_datetime)

        except ValueError:
            flash(
                "Please enter valid start and end dates.",
                "danger"
            )
            return redirect(
                url_for("timeline_admin.add_timeline")
            )

        if end <= start:
            flash(
                "End date and time must be after the start date and time.",
                "danger"
            )
            return redirect(
                url_for("timeline_admin.add_timeline")
            )

        existing = SystemTimeline.query.filter_by(
            setting_name=setting_name
        ).first()

        if existing:
            flash(
                "This timeline type has already been configured.",
                "warning"
            )
            return redirect(
                url_for("timeline_admin.add_timeline")
            )

        timeline = SystemTimeline()
        timeline.setting_name = setting_name
        timeline.start_datetime = start
        timeline.end_datetime = end
        timeline.is_active = True

        try:
            db.session.add(timeline)
            db.session.commit()

            flash(
                "Timeline created successfully!",
                "success"
            )

            return redirect(
                url_for("timeline_admin.timeline_list")
            )

        except Exception:
            db.session.rollback()

            flash(
                "Unable to create timeline.",
                "danger"
            )

    return render_template(
        "admin/add_timeline.html"
    )


                 
@timeline_admin_bp.route(
    "/edit/<int:timeline_id>",
    methods=["GET", "POST"]
)
@role_required("admin")
def edit_timeline(timeline_id):

    timeline = db.get_or_404(
        SystemTimeline,
        timeline_id
    )

    if request.method == "POST":

        start_datetime = request.form.get(
            "start_datetime", ""
        ).strip()

        end_datetime = request.form.get(
            "end_datetime", ""
        ).strip()

        if not start_datetime or not end_datetime:
            flash(
                "Please provide both dates.",
                "danger"
            )
            return redirect(
                url_for(
                    "timeline_admin.edit_timeline",
                    timeline_id=timeline_id
                )
            )

        try:
            start = datetime.fromisoformat(start_datetime)
            end = datetime.fromisoformat(end_datetime)

        except ValueError:
            flash(
                "Please enter valid dates and times.",
                "danger"
            )
            return redirect(
                url_for(
                    "timeline_admin.edit_timeline",
                    timeline_id=timeline_id
                )
            )

        if end <= start:
            flash(
                "End date and time must be after the start date and time.",
                "danger"
            )
            return redirect(
                url_for(
                    "timeline_admin.edit_timeline",
                    timeline_id=timeline_id
                )
            )

        timeline.start_datetime = start
        timeline.end_datetime = end

        try:
            db.session.commit()

            flash(
                "Timeline updated successfully!",
                "success"
            )

            return redirect(
                url_for("timeline_admin.timeline_list")
            )

        except Exception:
            db.session.rollback()

            flash(
                "Unable to update timeline.",
                "danger"
            )

    return render_template(
        "admin/edit_timeline.html",
        timeline=timeline
    )


                                   
@timeline_admin_bp.route(
    "/toggle/<int:timeline_id>",
    methods=["POST"]
)
@role_required("admin")
def toggle_timeline(timeline_id):

    timeline = db.get_or_404(
        SystemTimeline,
        timeline_id
    )

    timeline.is_active = not timeline.is_active

    try:
        db.session.commit()

        flash(
            "Timeline status updated successfully.",
            "success"
        )

    except Exception:
        db.session.rollback()

        flash(
            "Unable to update timeline status.",
            "danger"
        )

    return redirect(
        url_for("timeline_admin.timeline_list")
    )

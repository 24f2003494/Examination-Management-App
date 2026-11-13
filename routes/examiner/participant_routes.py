from flask import Blueprint, render_template
from flask_login import current_user

from models.slot import ExaminationSlot
from utils.decorators import role_required


participant_bp = Blueprint(
    "examiner_participants",
    __name__,
    url_prefix="/examiner/participants"
)


@participant_bp.route("/")
@role_required("examiner")
def participant_list():

    slots = ExaminationSlot.query.filter_by(
        examiner_id=current_user.id
    ).order_by(
        ExaminationSlot.slot_date,
        ExaminationSlot.start_time
    ).all()

    return render_template(
        "examiner/participants.html",
        slots=slots
    )
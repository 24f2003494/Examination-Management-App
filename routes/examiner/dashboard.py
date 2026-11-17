
from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import func

from extensions import db
from models.booking import Booking
from models.slot import ExaminationSlot
from models.evaluation import Evaluation
from models.examiner_assignment import ExaminerAssignment

from utils.decorators import role_required


examiner_bp = Blueprint("examiner", __name__, url_prefix="/examiner")


@examiner_bp.route("/dashboard")
@role_required("examiner")
def dashboard():

                                                   
    examiner_slots = ExaminationSlot.query.filter_by(
        examiner_id=current_user.id
    )

                                                      
    total_participants = (
        Booking.query
        .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
        .filter(
            ExaminationSlot.examiner_id == current_user.id,
            func.lower(Booking.status) != "cancelled"
        )
        .count()
    )

                                            
    evaluated_count = (
        Evaluation.query
        .join(Booking, Evaluation.booking_id == Booking.id)
        .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
        .filter(ExaminationSlot.examiner_id == current_user.id)
        .count()
    )

                                                                    
    pending_count = (
        Booking.query
        .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
        .outerjoin(Evaluation, Evaluation.booking_id == Booking.id)
        .filter(
            ExaminationSlot.examiner_id == current_user.id,
            func.lower(Booking.status) == "booked",
            Evaluation.id.is_(None)
        )
        .count()
    )

                                         
    participant_data = (
        db.session.query(
            ExaminationSlot.examination_id,
            func.count(Booking.id.distinct())
        )
        .join(Booking, Booking.slot_id == ExaminationSlot.id)
        .filter(
            ExaminationSlot.examiner_id == current_user.id,
            func.lower(Booking.status) != "cancelled"
        )
        .group_by(ExaminationSlot.examination_id)
        .all()
    )

                                              
    from models.examination import Examination

    examination_labels = []
    participant_values = []

    for examination_id, total in participant_data:
        examination = db.session.get(Examination, examination_id)

        if examination:
            examination_labels.append(examination.exam_name)
            participant_values.append(total)

    assigned_examinations = [
        assignment.examination
        for assignment in ExaminerAssignment.query.filter_by(
            examiner_id=current_user.id
        ).all()
    ]

    stats = {
        "assigned_examinations": len(assigned_examinations),
        "slots": examiner_slots.count(),
        "participants": total_participants,
        "evaluated": evaluated_count,
        "pending": pending_count
    }

    return render_template(
        "examiner/dashboard.html",
        stats=stats,
        assigned_examinations=assigned_examinations,
        examination_labels=examination_labels,
        participant_values=participant_values
    )

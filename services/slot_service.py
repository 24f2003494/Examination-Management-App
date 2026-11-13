
from datetime import date

from extensions import db
from models.examination import Examination
from models.slot import ExaminationSlot
from models.user import User
from models.examiner_assignment import ExaminerAssignment
from services.timeline_service import is_timeline_open


def create_examiner_slot(
    examination_id,
    examiner_id,
    slot_date,
    start_time,
    end_time,
    capacity
):
    if not is_timeline_open("slot_creation"):
        return False, "Slot creation is currently closed."

    examiner = User.query.filter_by(
        id=examiner_id,
        role="examiner",
        is_approved=True
    ).first()

    if not examiner:
        return False, "Valid approved examiner not found."

    examination = db.session.get(Examination, examination_id)

    if not examination:
        return False, "Examination not found."

    assignment = ExaminerAssignment.query.filter_by(
        examiner_id=examiner_id,
        examination_id=examination_id
    ).first()

    if not assignment:
        return False, "You are not assigned to this examination."

    if slot_date < date.today():
        return False, "You cannot create a slot in the past."

    if end_time <= start_time:
        return False, "End time must be later than start time."

    if capacity <= 0:
        return False, "Slot capacity must be greater than zero."

    # Prevent overlapping slots for the same examiner.
    overlapping_slot = ExaminationSlot.query.filter(
        ExaminationSlot.examiner_id == examiner_id,
        ExaminationSlot.slot_date == slot_date,
        ExaminationSlot.start_time < end_time,
        ExaminationSlot.end_time > start_time
    ).first()

    if overlapping_slot:
        return False, "This slot overlaps with another slot you created."

    slot = ExaminationSlot()
    slot.examination_id = examination_id
    slot.examiner_id = examiner_id
    slot.slot_date = slot_date
    slot.start_time = start_time
    slot.end_time = end_time
    slot.capacity = capacity
    slot.status = "available"

    try:
        db.session.add(slot)
        db.session.commit()
        return True, "Examination slot created successfully."

    except Exception:
        db.session.rollback()
        return False, "Unable to create the examination slot."

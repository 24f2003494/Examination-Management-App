
import math

from extensions import db

from models.booking import Booking
from models.evaluation import Evaluation
from models.rubric import ExaminationRubric
from models.rubric_evaluation import RubricEvaluation
from models.user import User
from models.slot import ExaminationSlot


def submit_evaluation(
    booking_id,
    examiner_id,
    rubric_marks,
    remarks
):
    booking = db.session.get(Booking, booking_id)

    if not booking:
        return False, "Booking not found."

    if booking.status != "booked":
        return False, "This booking is not active."

    if remarks and len(remarks) > 5000:
        return False, "Remarks cannot exceed 5000 characters."

    if not booking.slot:
        return False, "The examination slot could not be found."

    if booking.slot.examiner_id != examiner_id:
        return False, "You are not authorized to evaluate this student."

    examiner = User.query.filter_by(
        id=examiner_id,
        role="examiner",
        is_approved=True,
        account_active=True
    ).first()

    if not examiner:
        return False, "Approved examiner account not found."

    existing_evaluation = Evaluation.query.filter_by(
        booking_id=booking_id
    ).first()

    if existing_evaluation:
        return False, "This student has already been evaluated."

    examination = booking.slot.examination

    rubrics = ExaminationRubric.query.filter_by(
        examination_id=examination.id
    ).all()

    if not rubrics:
        return False, "No evaluation rubrics are configured."

    if set(rubric_marks.keys()) != {rubric.id for rubric in rubrics}:
        return False, "Please provide marks for every rubric."

    total_marks = 0

    for rubric in rubrics:
        try:
            marks = float(rubric_marks[rubric.id])
        except (ValueError, TypeError):
            return False, (
                f"Please enter valid marks for '{rubric.rubric_name}'."
            )

        if not math.isfinite(marks) or marks < 0 or marks > rubric.max_marks:
            return False, (
                f"Marks for '{rubric.rubric_name}' must be between "
                f"0 and {rubric.max_marks}."
            )

        total_marks += marks

    if total_marks > examination.total_marks:
        return False, "Total awarded marks exceed the examination maximum."

    try:
        evaluation = Evaluation()
        evaluation.booking_id = booking_id
        evaluation.examiner_id = examiner_id
        evaluation.marks_obtained = total_marks
        evaluation.remarks = remarks
        evaluation.is_published = False
        booking.status = "completed"

        db.session.add(evaluation)
        db.session.flush()

        for rubric in rubrics:
            rubric_score = RubricEvaluation()
            rubric_score.evaluation_id = evaluation.id
            rubric_score.rubric_id = rubric.id
            rubric_score.marks_awarded = float(
                rubric_marks[rubric.id]
            )

            db.session.add(rubric_score)

        db.session.commit()

        return True, "Rubric-based evaluation submitted successfully."

    except Exception:
        db.session.rollback()
        return False, "Unable to submit evaluation. Please try again."


def get_pending_evaluations(examiner_id):

    return (
        Booking.query
        .join(
            ExaminationSlot,
            Booking.slot_id == ExaminationSlot.id
        )
        .filter(
            Booking.status == "booked",
            ExaminationSlot.examiner_id == examiner_id,
            ~Booking.evaluation.has()
        )
        .order_by(Booking.booking_date)
        .all()
    )

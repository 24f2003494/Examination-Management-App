from datetime import datetime
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from flask_login import current_user

from extensions import db
from models.slot import ExaminationSlot
from models.examination import Examination
from models.user import User
from routes.api import role_required
from services.slot_service import create_examiner_slot
from services.timeline_service import is_timeline_open, has_timeline_started


slot_api = Blueprint("slot_api", __name__, url_prefix="/api/slots")


def slot_data(slot):
    return {
        "id": slot.id,
        "examination_id": slot.examination_id,
        "examination_name": slot.examination.exam_name,
        "examiner_id": slot.examiner_id,
        "examiner_name": slot.examiner.full_name,
        "slot_date": slot.slot_date.isoformat(),
        "start_time": slot.start_time.strftime("%H:%M"),
        "end_time": slot.end_time.strftime("%H:%M"),
        "capacity": slot.capacity,
        "status": slot.status
    }


def parse_slot_values(
    data: dict[str, Any],
    existing: Optional[ExaminationSlot] = None,
):
    try:
        if "slot_date" in data:
            slot_date = datetime.strptime(data["slot_date"], "%Y-%m-%d").date()
        elif existing is not None:
            slot_date = existing.slot_date
        else:
            return None

        if "start_time" in data:
            start_time = datetime.strptime(data["start_time"], "%H:%M").time()
        elif existing is not None:
            start_time = existing.start_time
        else:
            return None

        if "end_time" in data:
            end_time = datetime.strptime(data["end_time"], "%H:%M").time()
        elif existing is not None:
            end_time = existing.end_time
        else:
            return None
        capacity = int(data.get("capacity", existing.capacity if existing else 1))
    except (KeyError, ValueError, TypeError, AttributeError):
        return None

    if start_time >= end_time or capacity < 1:
        return None
    return slot_date, start_time, end_time, capacity


@slot_api.route("/", methods=["GET"])
@role_required("admin", "examiner", "student")
def get_slots():
    query = ExaminationSlot.query

    if (current_user.role or "").lower() == "examiner":
        query = query.filter_by(examiner_id=current_user.id)
    elif (current_user.role or "").lower() == "student":
        if not is_timeline_open("student_booking"):
            return jsonify([])
        today = datetime.now().date()
        now_time = datetime.now().time()
        query = query.filter(
            ExaminationSlot.status == "available",
            ExaminationSlot.slot_date >= today
        ).filter(
            (ExaminationSlot.slot_date > today)
            | (ExaminationSlot.start_time > now_time)
        )

    slots = query.order_by(
        ExaminationSlot.slot_date,
        ExaminationSlot.start_time
    ).all()
    return jsonify([slot_data(slot) for slot in slots])


@slot_api.route("/<int:slot_id>", methods=["GET"])
@role_required("admin", "examiner", "student")
def get_slot(slot_id):
    slot = db.session.get(ExaminationSlot, slot_id)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    if (current_user.role or "").lower() == "examiner" and slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot view this slot."}), 403
    if (current_user.role or "").lower() == "student":
        if not is_timeline_open("student_booking"):
            return jsonify({"error": "Student booking is currently closed."}), 403
        now = datetime.now()
        if (
            slot.status != "available"
            or slot.slot_date < now.date()
            or (slot.slot_date == now.date() and slot.start_time <= now.time())
        ):
            return jsonify({"error": "Slot is not available."}), 404

    return jsonify(slot_data(slot))


@slot_api.route("/", methods=["POST"])
@role_required("admin", "examiner")
def create_slot():
    data = request.get_json(silent=True) or {}
    try:
        examination_id = int(data["examination_id"])
        examiner_id = (
            current_user.id if (current_user.role or "").lower() == "examiner"
            else int(data["examiner_id"])
        )
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Valid examination_id and examiner_id are required."}), 400

    values = parse_slot_values(data)
    if values is None:
        return jsonify({"error": "Provide a valid date, time range, and positive capacity."}), 400
    slot_date, start_time, end_time, capacity = values

    if (current_user.role or "").lower() == "examiner":
        success, message = create_examiner_slot(
            examination_id, examiner_id, slot_date,
            start_time, end_time, capacity
        )
        if not success:
            return jsonify({"error": message}), 400
    else:
        examination = db.session.get(Examination, examination_id)
        examiner = User.query.filter_by(
            id=examiner_id, role="examiner", is_approved=True
        ).first()
        if not examination:
            return jsonify({"error": "Examination not found."}), 404
        if not examiner:
            return jsonify({"error": "Select an approved examiner."}), 400
        if slot_date < datetime.now().date() or (
            slot_date == datetime.now().date()
            and start_time <= datetime.now().time()
        ):
            return jsonify({"error": "Slot date and start time must be in the future."}), 400
        overlap = ExaminationSlot.query.filter(
            ExaminationSlot.examiner_id == examiner_id,
            ExaminationSlot.slot_date == slot_date,
            ExaminationSlot.start_time < end_time,
            ExaminationSlot.end_time > start_time
        ).first()
        if overlap:
            return jsonify({"error": "This slot overlaps another examiner slot."}), 409

                                                                        
                                                                       
                                                                           
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
        except Exception:
            db.session.rollback()
            return jsonify({"error": "Unable to create slot."}), 500
        return jsonify(slot_data(slot)), 201

    slot = ExaminationSlot.query.filter_by(
        examination_id=examination_id,
        examiner_id=examiner_id,
        slot_date=slot_date,
        start_time=start_time,
        end_time=end_time
    ).order_by(ExaminationSlot.id.desc()).first()
    return jsonify(slot_data(slot)), 201


@slot_api.route("/<int:slot_id>", methods=["PUT"])
@role_required("admin", "examiner")
def update_slot(slot_id):
    slot = db.session.get(ExaminationSlot, slot_id)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    if (current_user.role or "").lower() == "examiner" and slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot edit another examiner's slot."}), 403
    if (current_user.role or "").lower() == "examiner" and not current_user.is_approved:
        return jsonify({"error": "Your examiner account is not approved."}), 403
    if slot.bookings:
        return jsonify({"error": "A slot with booking history cannot be edited."}), 409
    if (current_user.role or "").lower() == "examiner" and (
        not is_timeline_open("slot_creation") or has_timeline_started("student_booking")
    ):
        return jsonify({"error": "Slot editing is currently closed."}), 403

    data = request.get_json(silent=True) or {}
    values = parse_slot_values(data, slot)
    if values is None:
        return jsonify({"error": "Invalid date, time range, or capacity."}), 400
    slot_date, start_time, end_time, capacity = values

    new_examiner_id = slot.examiner_id
    if (current_user.role or "").lower() == "admin" and "examiner_id" in data:
        try:
            new_examiner_id = int(data["examiner_id"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid examiner_id."}), 400
        examiner = User.query.filter_by(
            id=new_examiner_id, role="examiner", is_approved=True
        ).first()
        if not examiner:
            return jsonify({"error": "Select an approved examiner."}), 400

    if slot_date < datetime.now().date() or (
        slot_date == datetime.now().date()
        and start_time <= datetime.now().time()
    ):
        return jsonify({"error": "Slot date and start time must be in the future."}), 400
    overlap = ExaminationSlot.query.filter(
        ExaminationSlot.id != slot.id,
        ExaminationSlot.examiner_id == new_examiner_id,
        ExaminationSlot.slot_date == slot_date,
        ExaminationSlot.start_time < end_time,
        ExaminationSlot.end_time > start_time
    ).first()
    if overlap:
        return jsonify({"error": "This slot overlaps another examiner slot."}), 409

    slot.slot_date = slot_date
    slot.start_time = start_time
    slot.end_time = end_time
    slot.capacity = capacity
    slot.examiner_id = new_examiner_id

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to update slot."}), 500
    return jsonify(slot_data(slot))


@slot_api.route("/<int:slot_id>", methods=["DELETE"])
@role_required("admin", "examiner")
def delete_slot(slot_id):
    slot = db.session.get(ExaminationSlot, slot_id)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404
    if (current_user.role or "").lower() == "examiner" and slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot delete another examiner's slot."}), 403
    if (current_user.role or "").lower() == "examiner" and (
        not current_user.is_approved
        or not is_timeline_open("slot_creation")
        or has_timeline_started("student_booking")
    ):
        return jsonify({"error": "Slot deletion is currently closed."}), 403
    if slot.bookings:
        return jsonify({"error": "A slot with booking history cannot be deleted."}), 409

    try:
        db.session.delete(slot)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to delete slot."}), 500
    return jsonify({"message": "Slot deleted successfully."})

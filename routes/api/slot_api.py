
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import current_user
from extensions import db
from models.slot import ExaminationSlot
from models.examination import Examination
from models.examiner_assignment import ExaminerAssignment
from routes.api import role_required

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


@slot_api.route("/", methods=["GET"])
@role_required("Admin", "Examiner", "Student")
def get_slots():
    query = ExaminationSlot.query

    if current_user.role == "Examiner":
        query = query.filter_by(examiner_id=current_user.id)

    if current_user.role == "Student":
        query = query.filter_by(status="available")

    return jsonify([slot_data(slot) for slot in query.order_by(ExaminationSlot.slot_date).all()])


@slot_api.route("/<int:slot_id>", methods=["GET"])
@role_required("Admin", "Examiner", "Student")
def get_slot(slot_id):
    slot = db.session.get(ExaminationSlot, slot_id)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    if current_user.role == "Examiner" and slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot view this slot."}), 403

    return jsonify(slot_data(slot))


@slot_api.route("/", methods=["POST"])
@role_required("Admin", "Examiner")
def create_slot():
    data = request.get_json(silent=True) or {}

    try:
        examination_id = int(data["examination_id"])
        examiner_id = current_user.id if current_user.role == "Examiner" else int(data["examiner_id"])
        slot_date = datetime.strptime(data["slot_date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(data["start_time"], "%H:%M").time()
        end_time = datetime.strptime(data["end_time"], "%H:%M").time()
        capacity = int(data.get("capacity", 1))
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Provide valid examination_id, examiner_id (Admin only), date, times, and capacity."}), 400

    if not db.session.get(Examination, examination_id):
        return jsonify({"error": "Examination not found."}), 404

    if current_user.role == "Examiner":
        assignment = ExaminerAssignment.query.filter_by(
            examiner_id=current_user.id,
            examination_id=examination_id
        ).first()
        if not assignment:
            return jsonify({"error": "You are not assigned to this examination."}), 403

    if start_time >= end_time or capacity < 1:
        return jsonify({"error": "Invalid time range or capacity."}), 400

    slot = ExaminationSlot()
    slot.examination_id = examination_id
    slot.examiner_id = examiner_id
    slot.slot_date = slot_date
    slot.start_time = start_time
    slot.end_time = end_time
    slot.capacity = capacity
    slot.status = "available"
    db.session.add(slot)
    db.session.commit()
    return jsonify(slot_data(slot)), 201


@slot_api.route("/<int:slot_id>", methods=["PUT"])
@role_required("Admin", "Examiner")
def update_slot(slot_id):
    slot = db.session.get(ExaminationSlot, slot_id)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    if current_user.role == "Examiner" and slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot edit another examiner's slot."}), 403

    if slot.bookings:
        return jsonify({"error": "A slot with bookings cannot be edited through this API."}), 409

    data = request.get_json(silent=True) or {}

    try:
        if "slot_date" in data:
            slot.slot_date = datetime.strptime(data["slot_date"], "%Y-%m-%d").date()
        if "start_time" in data:
            slot.start_time = datetime.strptime(data["start_time"], "%H:%M").time()
        if "end_time" in data:
            slot.end_time = datetime.strptime(data["end_time"], "%H:%M").time()
        if "capacity" in data:
            slot.capacity = int(data["capacity"])
        if current_user.role == "Admin" and "examiner_id" in data:
            slot.examiner_id = int(data["examiner_id"])

        if slot.start_time >= slot.end_time or slot.capacity < 1:
            return jsonify({"error": "Invalid time range or capacity."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date, time, or capacity."}), 400

    db.session.commit()
    return jsonify(slot_data(slot))


@slot_api.route("/<int:slot_id>", methods=["DELETE"])
@role_required("Admin", "Examiner")
def delete_slot(slot_id):
    slot = db.session.get(ExaminationSlot, slot_id)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    if current_user.role == "Examiner" and slot.examiner_id != current_user.id:
        return jsonify({"error": "You cannot delete another examiner's slot."}), 403

    if slot.bookings:
        return jsonify({"error": "A slot with booking history cannot be deleted."}), 409

    db.session.delete(slot)
    db.session.commit()
    return jsonify({"message": "Slot deleted successfully."})

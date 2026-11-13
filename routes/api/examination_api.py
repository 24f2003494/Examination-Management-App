
from flask import Blueprint, jsonify, request
from extensions import db
from models.examination import Examination
from models.course import Course
from routes.api import role_required

examination_api = Blueprint("examination_api", __name__, url_prefix="/api/examinations")


def examination_data(exam):
    return {
        "id": exam.id,
        "exam_name": exam.exam_name,
        "description": exam.description,
        "course_id": exam.course_id,
        "course_name": exam.course.course_name,
        "total_marks": exam.total_marks,
        "passing_marks": exam.passing_marks
    }


@examination_api.route("/", methods=["GET"])
@role_required("Admin", "Examiner", "Student")
def get_examinations():
    exams = Examination.query.order_by(Examination.id.desc()).all()
    return jsonify([examination_data(exam) for exam in exams])


@examination_api.route("/<int:exam_id>", methods=["GET"])
@role_required("Admin", "Examiner", "Student")
def get_examination(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return jsonify({"error": "Examination not found"}), 404
    return jsonify(examination_data(exam))


@examination_api.route("/", methods=["POST"])
@role_required("Admin")
def create_examination():
    data = request.get_json(silent=True) or {}

    required = ["exam_name", "course_id", "total_marks", "passing_marks"]
    if any(data.get(field) in (None, "") for field in required):
        return jsonify({"error": "All required fields must be provided."}), 400

    try:
        course_id = int(data["course_id"])
        total_marks = int(data["total_marks"])
        passing_marks = int(data["passing_marks"])
    except (ValueError, TypeError):
        return jsonify({"error": "Course ID and marks must be numbers."}), 400

    if not db.session.get(Course, course_id):
        return jsonify({"error": "Course not found."}), 404
    if total_marks <= 0 or passing_marks < 0 or passing_marks > total_marks:
        return jsonify({"error": "Invalid marks range."}), 400

    exam = Examination()
    exam.exam_name = str(data["exam_name"]).strip()
    exam.description = data.get("description", "")
    exam.course_id = course_id
    exam.total_marks = total_marks
    exam.passing_marks = passing_marks
    db.session.add(exam)
    db.session.commit()
    return jsonify(examination_data(exam)), 201


@examination_api.route("/<int:exam_id>", methods=["PUT"])
@role_required("Admin")
def update_examination(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return jsonify({"error": "Examination not found"}), 404

    data = request.get_json(silent=True) or {}
    try:
        if "course_id" in data:
            course_id = int(data["course_id"])
            if not db.session.get(Course, course_id):
                return jsonify({"error": "Course not found"}), 404
            exam.course_id = course_id

        total = int(data.get("total_marks", exam.total_marks))
        passing = int(data.get("passing_marks", exam.passing_marks))
        if total <= 0 or passing < 0 or passing > total:
            return jsonify({"error": "Invalid marks range."}), 400

        exam.exam_name = str(data.get("exam_name", exam.exam_name)).strip()
        exam.description = data.get("description", exam.description)
        exam.total_marks = total
        exam.passing_marks = passing
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric values."}), 400

    db.session.commit()
    return jsonify(examination_data(exam))


@examination_api.route("/<int:exam_id>", methods=["DELETE"])
@role_required("Admin")
def delete_examination(exam_id):
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return jsonify({"error": "Examination not found"}), 404

    if exam.slots or exam.rubrics or exam.examiner_assignments:
        return jsonify({"error": "Cannot delete an examination with related slots, rubrics, or examiner assignments."}), 409

    db.session.delete(exam)
    db.session.commit()
    return jsonify({"message": "Examination deleted successfully."})


from flask import Blueprint, render_template, request
from models.examination import Examination
from models.course import Course
from utils.decorators import role_required

student_exam_bp = Blueprint(
    "student_exams",
    __name__,
    url_prefix="/student/examinations"
)

@student_exam_bp.route("/")
@role_required("student")
def exam_list():
    search = request.args.get("search", "").strip()
    course_id = request.args.get("course_id", "").strip()

                                                                                
    query = Examination.query.filter(Examination.status.in_(["Slot Creation", "Booking Open", "Closed", "Completed"]))

    if search:
        query = query.filter(
            Examination.exam_name.ilike(f"%{search}%")
        )

    if course_id:
        try:
            selected_course_id = int(course_id)
        except ValueError:
            selected_course_id = None

        if selected_course_id is not None:
            query = query.filter(
                Examination.course_id == selected_course_id
            )

    examinations = query.all()
    courses = Course.query.order_by(Course.course_name).all()

    return render_template(
        "student/examinations.html",
        examinations=examinations,
        courses=courses
    )

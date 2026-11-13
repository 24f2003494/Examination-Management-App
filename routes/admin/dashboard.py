from flask import Blueprint, render_template

from models.user import User
from models.course import Course
from models.examination import Examination
from models.slot import ExaminationSlot
from models.booking import Booking

from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():

    counts = {
        "courses": Course.query.count(),
        "examinations": Examination.query.count(),
        "examiners": User.query.filter_by(role="examiner").count(),
        "students": User.query.filter_by(role="student").count(),
        "slots": ExaminationSlot.query.count(),
        "bookings": Booking.query.count()
    }

    examinations = Examination.query.all()

    return render_template(
        "admin/dashboard.html",
        counts=counts,
        examinations=examinations
    )
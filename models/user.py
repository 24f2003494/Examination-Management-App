
from flask_login import UserMixin
from extensions import db
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship
from flask_login import UserMixin
from extensions import db

if TYPE_CHECKING:
    from models.examiner import ExaminerProfile
from sqlalchemy.orm import Mapped, relationship
from typing import Optional
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    is_approved = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    examiner_profile: Mapped[Optional["ExaminerProfile"]] = relationship(
    "ExaminerProfile",
    back_populates="user",
    uselist=False
)

    examination_slots = db.relationship(
        "ExaminationSlot",
        back_populates="examiner"
    )

    bookings = db.relationship(
        "Booking",
        back_populates="student",
        foreign_keys="Booking.student_id"
    )

    evaluations = db.relationship(
        "Evaluation",
        back_populates="examiner",
        foreign_keys="Evaluation.examiner_id"
    )

    def __repr__(self):
        return f"<User {self.email}>"


from extensions import db
from sqlalchemy import UniqueConstraint

class Booking(db.Model):

    __tablename__ = "bookings"
    __table_args__ = (
    UniqueConstraint(
        "student_id",
        "slot_id",
        name="uq_student_slot"
    ),
)
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    slot_id = db.Column(
        db.Integer,
        db.ForeignKey("examination_slots.id"),
        nullable=False
    )

    booking_date = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now()
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="booked"
    )

    student = db.relationship(
        "User",
        back_populates="bookings",
        foreign_keys=[student_id]
    )

    slot = db.relationship(
        "ExaminationSlot",
        back_populates="bookings"
    )

    evaluation = db.relationship(
        "Evaluation",
        back_populates="booking",
        uselist=False
    )

    def __repr__(self):
        return f"<Booking {self.id}>"

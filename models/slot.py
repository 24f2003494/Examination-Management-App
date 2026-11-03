
from extensions import db


class ExaminationSlot(db.Model):

    __tablename__ = "examination_slots"

    id = db.Column(db.Integer, primary_key=True)

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    examiner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    slot_date = db.Column(db.Date, nullable=False)

    start_time = db.Column(db.Time, nullable=False)

    end_time = db.Column(db.Time, nullable=False)

    capacity = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="available"
    )

    examination = db.relationship(
        "Examination",
        back_populates="slots"
    )

    examiner = db.relationship(
        "User",
        back_populates="examination_slots"
    )
    bookings = db.relationship(
    "Booking",
    back_populates="slot"
)   
    def __repr__(self):
        return f"<ExaminationSlot {self.id}>"

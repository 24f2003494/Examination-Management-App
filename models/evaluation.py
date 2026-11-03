
from extensions import db


class Evaluation(db.Model):

    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id"),
        unique=True,
        nullable=False
    )

    examiner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    marks_obtained = db.Column(
        db.Float,
        nullable=False
    )

    remarks = db.Column(
        db.Text,
        nullable=True
    )

    evaluated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now()
    )

    is_published = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    booking = db.relationship(
        "Booking",
        back_populates="evaluation"
    )

    examiner = db.relationship(
        "User",
        back_populates="evaluations",
        foreign_keys=[examiner_id]
    )

    def __repr__(self):
        return f"<Evaluation {self.id}>"

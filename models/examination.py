
from extensions import db


class Examination(db.Model):

    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)

    exam_name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(db.Text, nullable=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    total_marks = db.Column(
        db.Integer,
        nullable=False,
        default=100
    )

    passing_marks = db.Column(
        db.Integer,
        nullable=False,
        default=40
    )

    course = db.relationship(
        "Course",
        back_populates="examinations"
    )

    rubrics = db.relationship(
        "ExaminationRubric",
        back_populates="examination",
        cascade="all, delete-orphan"
    )
    slots = db.relationship(
    "ExaminationSlot",
    back_populates="examination"
)
    def __repr__(self):
        return f"<Examination {self.exam_name}>"

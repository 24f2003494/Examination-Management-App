
from extensions import db


class ExaminationRubric(db.Model):

    __tablename__ = "examination_rubrics"

    id = db.Column(db.Integer, primary_key=True)

    criterion = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(db.Text, nullable=True)

    max_marks = db.Column(
        db.Integer,
        nullable=False
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    examination = db.relationship(
        "Examination",
        back_populates="rubrics"
    )

    def __repr__(self):
        return f"<Rubric {self.criterion}>"

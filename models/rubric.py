
from extensions import db


class ExaminationRubric(db.Model):
    __tablename__ = "examination_rubrics"

    id = db.Column(db.Integer, primary_key=True)

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    rubric_name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    max_marks = db.Column(
        db.Float,
        nullable=False
    )

    examination = db.relationship(
        "Examination",
        back_populates="rubrics"
    )

    rubric_scores = db.relationship(
        "RubricEvaluation",
        back_populates="rubric",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ExaminationRubric {self.rubric_name}>"

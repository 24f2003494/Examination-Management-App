from extensions import db


class RubricEvaluation(db.Model):

    __tablename__ = "rubric_evaluations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    evaluation_id = db.Column(
        db.Integer,
        db.ForeignKey("evaluations.id"),
        nullable=False
    )

    rubric_id = db.Column(
        db.Integer,
        db.ForeignKey("examination_rubrics.id"),
        nullable=False
    )

    marks_awarded = db.Column(
        db.Float,
        nullable=False
    )

    evaluation = db.relationship(
        "Evaluation",
        back_populates="rubric_scores"
    )

    rubric = db.relationship(
        "ExaminationRubric"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "evaluation_id",
            "rubric_id",
            name="uq_evaluation_rubric"
        ),
    )

    def __repr__(self):
        return f"<RubricEvaluation {self.rubric_id}>"
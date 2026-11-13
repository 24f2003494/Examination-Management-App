from extensions import db


class ExaminerAssignment(db.Model):

    __tablename__ = "examiner_assignments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    examiner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    assigned_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now()
    )

    examiner = db.relationship(
        "User",
        back_populates="examiner_assignments",
        foreign_keys=[examiner_id]
    )

    examination = db.relationship(
        "Examination",
        back_populates="examiner_assignments",
        foreign_keys=[examination_id]
    )

    __table_args__ = (
        db.UniqueConstraint(
            "examiner_id",
            "examination_id",
            name="uq_examiner_examination"
        ),
    )

    def __repr__(self):
        return f"<ExaminerAssignment {self.examiner_id}-{self.examination_id}>"
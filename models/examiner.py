
from extensions import db


class ExaminerProfile(db.Model):

    __tablename__ = "examiner_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    qualification = db.Column(
        db.String(150),
        nullable=True
    )

    specialization = db.Column(
        db.String(150),
        nullable=True
    )

    experience_years = db.Column(
        db.Integer,
        nullable=True
    )

    user = db.relationship(
        "User",
        back_populates="examiner_profile"
    )

    def __repr__(self):
        return f"<ExaminerProfile {self.user_id}>"

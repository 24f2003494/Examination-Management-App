
from extensions import db


class Course(db.Model):

    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)

    course_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    course_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    description = db.Column(db.Text, nullable=True)

    examinations = db.relationship(
        "Examination",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Course {self.course_code}>"


from flask_login import UserMixin

from extensions import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)

    is_approved = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    def __repr__(self):
        return f"<User {self.email}>"

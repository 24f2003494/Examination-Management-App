
from extensions import db


class SystemTimeline(db.Model):

    __tablename__ = "system_timelines"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    setting_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    start_datetime = db.Column(
        db.DateTime,
        nullable=False
    )

    end_datetime = db.Column(
        db.DateTime,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    def __repr__(self):
        return f"<SystemTimeline {self.setting_name}>"

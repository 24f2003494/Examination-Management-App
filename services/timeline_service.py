from datetime import datetime

from models.timeline import SystemTimeline


def is_timeline_open(setting_name):
    timeline = SystemTimeline.query.filter_by(
        setting_name=setting_name,
        is_active=True
    ).first()

    if not timeline:
        return False

    current_datetime = datetime.now()

    return (
        timeline.start_datetime
        <= current_datetime
        <= timeline.end_datetime
    )


def has_timeline_started(setting_name):
    timeline = SystemTimeline.query.filter_by(
        setting_name=setting_name,
        is_active=True
    ).first()

    if not timeline:
        return False

    return datetime.now() >= timeline.start_datetime
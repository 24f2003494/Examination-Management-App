
from flask import url_for


def get_dashboard_url(role):

    dashboard_routes = {
        "admin": "admin.dashboard",
        "examiner": "examiner.dashboard",
        "student": "student.dashboard"
    }

    endpoint = dashboard_routes.get(role)

    if endpoint:
        return url_for(endpoint)

    return url_for("main.home")

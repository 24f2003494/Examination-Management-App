
from functools import wraps

from flask import jsonify
from flask_login import current_user, login_required


def role_required(*roles):
    """Require login and one of the specified user roles."""
    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role.lower() not in [role.lower() for role in roles]:
                
                return jsonify({"error": "You do not have permission to perform this action."}), 403
            if current_user.role.lower() == "examiner" and not current_user.is_approved:
                return jsonify({"error": "Your examiner account is not approved."}), 403
            return view_function(*args, **kwargs)
        return wrapped
    return decorator

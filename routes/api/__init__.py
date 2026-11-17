from functools import wraps

from flask import jsonify
from flask_login import current_user


def role_required(*roles):
    """Protect API routes with JSON responses and role/account checks."""
    allowed = {role.lower() for role in roles}

    def decorator(view_function):
        @wraps(view_function)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication is required."}), 401

            user_role = (current_user.role or "").lower()
            if user_role not in allowed:
                return jsonify({"error": "You do not have permission to perform this action."}), 403

            if user_role in {"student", "examiner"} and not current_user.account_active:
                return jsonify({"error": "Your account has been deactivated."}), 403

            if user_role == "examiner" and not current_user.is_approved:
                return jsonify({"error": "Your examiner account is awaiting approval."}), 403

            return view_function(*args, **kwargs)
        return wrapped
    return decorator

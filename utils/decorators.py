from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*allowed_roles):
    normalized_roles = {role.lower() for role in allowed_roles}

    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            user_role = (current_user.role or "").lower()

            if user_role not in normalized_roles:
                abort(403)

                                                                           
                                                                            
            if user_role in {"student", "examiner"} and (
                not current_user.account_active
                or (user_role == "examiner" and not current_user.is_approved)
            ):
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator

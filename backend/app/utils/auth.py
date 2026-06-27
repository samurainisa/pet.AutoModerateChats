from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models import User


ROLE_PRIORITY = {"user": 1, "moderator": 2, "admin": 3}


def get_current_user() -> User | None:
    identity = get_jwt_identity()
    if identity is None:
        return None
    return db.session.get(User, int(identity))


def roles_required(*roles):
    minimum = max((ROLE_PRIORITY.get(role, 0) for role in roles), default=0)

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if user is None:
                return jsonify({"error": "user_not_found"}), 401

            if user.is_temporarily_blocked() and user.role == "user":
                return jsonify({"error": "user_blocked", "blocked_until": user.blocked_until.isoformat() if user.blocked_until else None}), 403

            if ROLE_PRIORITY.get(user.role, 0) < minimum:
                return jsonify({"error": "forbidden"}), 403

            return fn(*args, **kwargs)

        return wrapped

    return decorator

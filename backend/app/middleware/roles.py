"""
Role-based access helpers
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User

ROLE_OPTIONS = ['admin', 'planning', 'warehouse', 'purchasing', 'production', 'logistics']


def get_current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def require_roles(*roles):
    allowed = set(roles)

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or not user.is_active:
                return jsonify({'error': 'No autorizado'}), 403
            if user.role == 'admin':
                return f(*args, **kwargs)
            if user.role not in allowed:
                return jsonify({'error': 'No autorizado'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

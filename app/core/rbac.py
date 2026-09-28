from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from ..models.rbac import User

def require_permission(code):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            from ..extensions import db
            user = db.session.get(User, int(get_jwt_identity()))
            if not user or not user.is_active:
                return jsonify({"error": {"code": "AUTH_UNAUTHORIZED", "message": "User not found or inactive."}}), 401
            if not user.has_permission(code):
                return jsonify({"error": {"code": "RBAC_PERMISSION_DENIED", "message": f"Missing permission: {code}"}}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

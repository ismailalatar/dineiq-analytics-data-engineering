from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt_identity)
from ..extensions import db, limiter
from ..models.rbac import User
from ..services.audit_service import log_action
from ..core.errors import AppError

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    username = (d.get("username") or "").strip()
    password = d.get("password") or ""
    if not email or not username or not password:
        raise AppError("VALIDATION_ERROR", "email, username, password required.")
    if len(password) < 8:
        raise AppError("VALIDATION_ERROR", "Password must be at least 8 characters.")
    if User.query.filter_by(email=email).first():
        raise AppError("CONFLICT_DUPLICATE", "Email already registered.", 409)
    if User.query.filter_by(username=username).first():
        raise AppError("CONFLICT_DUPLICATE", "Username already taken.", 409)
    u = User(email=email, username=username, full_name=d.get("full_name", ""))
    u.set_password(password)
    db.session.add(u); db.session.commit()
    log_action("USER_REGISTERED", f"users:{u.id}", "success", {"email": email}, user_id=u.id)
    return jsonify({"message": "User registered.", "user": u.to_dict()}), 201

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    d = request.get_json() or {}
    ident = (d.get("email") or d.get("username") or "").strip()
    pwd = d.get("password") or ""
    if not ident or not pwd:
        raise AppError("VALIDATION_ERROR", "Credentials required.")
    u = User.query.filter((User.email == ident.lower()) | (User.username == ident)).first()
    if not u:
        log_action("LOGIN_FAILED", "auth", "failure", {"identifier": ident}, user_id=None)
        raise AppError("AUTH_INVALID_CREDENTIALS", "Invalid credentials.", 401)
    if u.is_locked:
        log_action("LOGIN_BLOCKED", "auth", "denied", {"user_id": u.id}, user_id=u.id)
        raise AppError("AUTH_ACCOUNT_LOCKED", "Account locked.", 403)
    if not u.check_password(pwd):
        u.failed_attempts = (u.failed_attempts or 0) + 1
        if u.failed_attempts >= 5: u.is_locked = True
        db.session.commit()
        log_action("LOGIN_FAILED", "auth", "failure", {"user_id": u.id}, user_id=u.id)
        raise AppError("AUTH_INVALID_CREDENTIALS", "Invalid credentials.", 401)
    u.failed_attempts = 0
    u.last_login_at = datetime.utcnow()
    db.session.commit()
    log_action("LOGIN_SUCCESS", "auth", "success", {"user_id": u.id}, user_id=u.id)
    return jsonify({
        "access_token": create_access_token(identity=str(u.id)),
        "refresh_token": create_refresh_token(identity=str(u.id)),
        "user": u.to_dict(),
    })

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    u = db.session.get(User, int(get_jwt_identity()))
    if not u: raise AppError("RESOURCE_NOT_FOUND", "User not found.", 404)
    return jsonify(u.to_dict())

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    return jsonify({"access_token": create_access_token(identity=get_jwt_identity())})

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    uid = get_jwt_identity()
    log_action("LOGOUT", "auth", "success", {"user_id": uid}, user_id=int(uid))
    return jsonify({"message": "Logged out."})

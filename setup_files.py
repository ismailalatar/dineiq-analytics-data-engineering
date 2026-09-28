import os, textwrap

ROOT = r"D:\DineIQ"

FILES = {}

FILES[r".env"] = """SECRET_KEY=dev_secret_change_me
JWT_SECRET_KEY=dev_jwt_change_me
DATABASE_URL=sqlite:///dineiq_app.db
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
"""

FILES[r".gitignore"] = """venv/
__pycache__/
*.pyc
*.db
.env
instance/
.pytest_cache/
"""

FILES[r"requirements.txt"] = """Flask==3.1.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-JWT-Extended==4.7.1
Flask-Bcrypt==1.0.1
Flask-Limiter==3.9.2
python-dotenv==1.0.1
pandas==2.2.3
openpyxl==3.1.5
pytest==8.3.4
"""

FILES[r"run.py"] = """from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
"""

FILES[r"seed.py"] = '''from app import create_app
from app.extensions import db
from app.models.rbac import User, Role, Permission

PERMISSIONS = [
    "users:read","users:write","roles:read","roles:write",
    "locations:read","locations:write","menu:read","menu:write",
    "pricing:read","pricing:write","orders:read",
    "promotions:read","promotions:write","ratings:read",
    "inventory:read","inventory:write","wastage:read","wastage:write",
    "analytics:read","recommendations:read","recommendations:write",
    "audit:read","export:csv","export:xlsx","models:read","models:write",
]

ROLE_PERMS = {
    "restaurant_manager": [
        "roles:read","locations:read","menu:read","menu:write","pricing:read","pricing:write",
        "orders:read","promotions:read","promotions:write","ratings:read","inventory:read",
        "inventory:write","wastage:read","wastage:write","analytics:read",
        "recommendations:read","export:csv","export:xlsx","models:read",
    ],
    "analyst": [
        "roles:read","locations:read","menu:read","pricing:read","orders:read",
        "promotions:read","ratings:read","inventory:read","wastage:read","analytics:read",
        "recommendations:read","recommendations:write","export:csv","export:xlsx",
        "models:read","models:write",
    ],
    "regional_manager": [
        "roles:read","locations:read","menu:read","pricing:read","orders:read",
        "promotions:read","ratings:read","inventory:read","wastage:read","analytics:read",
        "recommendations:read","audit:read","export:csv","export:xlsx","models:read",
    ],
    "administrator": PERMISSIONS,
}

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        pmap = {}
        for code in PERMISSIONS:
            p = Permission.query.filter_by(code=code).first() or Permission(code=code)
            if not p.id: db.session.add(p)
            pmap[code] = p
        db.session.commit()
        rmap = {}
        for rn, codes in ROLE_PERMS.items():
            r = Role.query.filter_by(name=rn).first() or Role(name=rn)
            if not r.id: db.session.add(r)
            r.permissions = [pmap[c] for c in codes]
            rmap[rn] = r
        db.session.commit()
        if not User.query.filter_by(email="admin@dineiq.local").first():
            u = User(email="admin@dineiq.local", username="admin", full_name="System Admin")
            u.set_password("Admin@12345")
            u.roles = [rmap["administrator"]]
            db.session.add(u); db.session.commit()
            print("Admin: admin@dineiq.local / Admin@12345")
        print("Seed OK.")

if __name__ == "__main__":
    seed()
'''

FILES[r"app\__init__.py"] = """from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, bcrypt, limiter

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    from .api.auth import auth_bp
    from .api.admin import admin_bp
    from .api.audit import audit_bp
    from .api.export import export_bp

    app.register_blueprint(auth_bp,   url_prefix="/api/v1/auth")
    app.register_blueprint(admin_bp,  url_prefix="/api/v1")
    app.register_blueprint(audit_bp,  url_prefix="/api/v1/audit")
    app.register_blueprint(export_bp, url_prefix="/api/v1/export")

    from .core.errors import register_error_handlers
    register_error_handlers(app)

    from .middleware.audit import init_audit_middleware
    init_audit_middleware(app)

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "DineIQ Backend"}

    return app
"""

FILES[r"app\config.py"] = """import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dineiq_app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev")
    JWT_ACCESS_TOKEN_EXPIRES = 900
    JWT_REFRESH_TOKEN_EXPIRES = 604800
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", 12))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
"""

FILES[r"app\extensions.py"] = """from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)
"""

FILES[r"app\models\__init__.py"] = """from .rbac import User, Role, Permission, user_roles, role_permissions
from .audit import AuditLog
from .reference import (Restaurant, MenuCategory, MenuItem, PricingHistory,
                        Customer, Order, OrderItem, Promotion, Rating, Inventory, Wastage)
from .integration import Recommendation, ModelVersion, ExportLog
"""

FILES[r"app\models\rbac.py"] = """from datetime import datetime
from ..extensions import db, bcrypt

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    users = db.relationship("User", secondary=user_roles, back_populates="roles")
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(db.Model):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    is_active = db.Column(db.Boolean, default=True)
    is_locked = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    roles = db.relationship("Role", secondary=user_roles, back_populates="users")

    def set_password(self, raw):
        self.password_hash = bcrypt.generate_password_hash(raw).decode("utf-8")

    def check_password(self, raw):
        return bcrypt.check_password_hash(self.password_hash, raw)

    def has_permission(self, code):
        return any(p.code == code for r in self.roles for p in r.permissions)

    def permissions_list(self):
        return sorted({p.code for r in self.roles for p in r.permissions})

    def to_dict(self):
        return {
            "id": self.id, "email": self.email, "username": self.username,
            "full_name": self.full_name, "is_active": self.is_active,
            "roles": [r.name for r in self.roles],
            "permissions": self.permissions_list(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
"""

FILES[r"app\models\audit.py"] = """from datetime import datetime
from ..extensions import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    action = db.Column(db.String(80), nullable=False, index=True)
    resource = db.Column(db.String(120), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    request_id = db.Column(db.String(36), index=True)
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "action": self.action,
            "resource": self.resource, "result": self.result,
            "ip_address": self.ip_address, "request_id": self.request_id,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
"""

FILES[r"app\models\reference.py"] = """from datetime import datetime
from ..extensions import db

class Restaurant(db.Model):
    __tablename__ = "restaurants"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(80))
    is_active = db.Column(db.Boolean, default=True)

class MenuCategory(db.Model):
    __tablename__ = "menu_categories"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)

class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("menu_categories.id"))
    base_price = db.Column(db.Numeric(10, 2))
    base_cost = db.Column(db.Numeric(10, 2))
    is_available = db.Column(db.Boolean, default=True)

class PricingHistory(db.Model):
    __tablename__ = "pricing_history"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    old_price = db.Column(db.Numeric(10, 2))
    new_price = db.Column(db.Numeric(10, 2), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False)

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(40), unique=True, nullable=False)
    segment = db.Column(db.String(40))

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(40), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    channel = db.Column(db.String(30))
    status = db.Column(db.String(20))
    total_amount = db.Column(db.Numeric(12, 2))
    placed_at = db.Column(db.DateTime, nullable=False, index=True)

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"))
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2))
    line_total = db.Column(db.Numeric(12, 2))

class Promotion(db.Model):
    __tablename__ = "promotions"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120))
    discount_pct = db.Column(db.Numeric(5, 2))
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    score = db.Column(db.SmallInteger)
    created_at = db.Column(db.DateTime, nullable=False)

class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    stock_qty = db.Column(db.Numeric(12, 2))
    reorder_lvl = db.Column(db.Numeric(12, 2))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Wastage(db.Model):
    __tablename__ = "wastage"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    quantity = db.Column(db.Numeric(12, 2))
    cost = db.Column(db.Numeric(12, 2))
    reason = db.Column(db.String(120))
    wasted_at = db.Column(db.DateTime, nullable=False)
"""

FILES[r"app\models\integration.py"] = """from datetime import datetime
from ..extensions import db

class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(40))
    entity_id = db.Column(db.String(60))
    action = db.Column(db.String(120))
    priority = db.Column(db.String(10))
    evidence_json = db.Column(db.Text, nullable=False)
    model_version = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ModelVersion(db.Model):
    __tablename__ = "model_versions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    version = db.Column(db.String(40), nullable=False)
    pipeline = db.Column(db.String(20))
    metrics_json = db.Column(db.Text)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)

class ExportLog(db.Model):
    __tablename__ = "export_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    report_name = db.Column(db.String(80))
    format = db.Column(db.String(10))
    row_count = db.Column(db.Integer)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
"""

FILES[r"app\core\__init__.py"] = ""

FILES[r"app\core\errors.py"] = """from flask import jsonify
from werkzeug.exceptions import HTTPException

ERROR_CODES = {
    400: "VALIDATION_ERROR", 401: "AUTH_UNAUTHORIZED",
    403: "RBAC_PERMISSION_DENIED", 404: "RESOURCE_NOT_FOUND",
    409: "CONFLICT_DUPLICATE", 422: "UNPROCESSABLE_ENTITY",
    429: "RATE_LIMIT_EXCEEDED", 500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}

class AppError(Exception):
    def __init__(self, code, message, status=400, details=None):
        self.code, self.message, self.status, self.details = code, message, status, details

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app(e):
        return jsonify({"error": {"code": e.code, "message": e.message, "details": e.details}}), e.status

    @app.errorhandler(HTTPException)
    def _http(e):
        return jsonify({"error": {"code": ERROR_CODES.get(e.code, "HTTP_ERROR"), "message": e.description, "details": None}}), e.code

    @app.errorhandler(Exception)
    def _unexpected(e):
        app.logger.exception("Unhandled")
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Unexpected error.", "details": None}}), 500
"""

FILES[r"app\core\rbac.py"] = """from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from ..models.rbac import User

def require_permission(code):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = User.query.get(get_jwt_identity())
            if not user or not user.is_active:
                return jsonify({"error": {"code": "AUTH_UNAUTHORIZED", "message": "User not found or inactive."}}), 401
            if not user.has_permission(code):
                return jsonify({"error": {"code": "RBAC_PERMISSION_DENIED", "message": f"Missing permission: {code}"}}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
"""

FILES[r"app\services\__init__.py"] = ""

FILES[r"app\services\audit_service.py"] = """import json
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from ..extensions import db
from ..models.audit import AuditLog

def _uid():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None

def log_action(action, resource, result="success", metadata=None, user_id=None):
    if user_id is None:
        user_id = _uid()
    log = AuditLog(
        user_id=user_id, action=action, resource=resource, result=result,
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get("User-Agent") if request else None,
        request_id=getattr(g, "request_id", None),
        metadata_json=json.dumps(metadata, default=str) if metadata else None,
    )
    db.session.add(log)
    db.session.commit()
    return log
"""

FILES[r"app\middleware\__init__.py"] = ""

FILES[r"app\middleware\audit.py"] = """import uuid
from flask import g

def init_audit_middleware(app):
    @app.before_request
    def _rid():
        g.request_id = str(uuid.uuid4())

    @app.after_request
    def _attach(response):
        if hasattr(g, "request_id"):
            response.headers["X-Request-Id"] = g.request_id
        return response
"""

FILES[r"app\api\__init__.py"] = ""

FILES[r"app\api\auth.py"] = """from datetime import datetime
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
    u = User.query.get(int(get_jwt_identity()))
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
"""

FILES[r"app\api\admin.py"] = """from flask import Blueprint, request, jsonify
from ..extensions import db
from ..core.rbac import require_permission
from ..models.reference import Restaurant, MenuItem

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/locations", methods=["GET"])
@require_permission("locations:read")
def list_locations():
    return jsonify([{"id": r.id, "code": r.code, "name": r.name, "city": r.city}
                    for r in Restaurant.query.all()])

@admin_bp.route("/locations", methods=["POST"])
@require_permission("locations:write")
def create_location():
    d = request.get_json() or {}
    r = Restaurant(code=d["code"], name=d["name"], city=d.get("city"))
    db.session.add(r); db.session.commit()
    return jsonify({"id": r.id}), 201

@admin_bp.route("/menu_items", methods=["GET"])
@require_permission("menu:read")
def list_menu():
    return jsonify([{"id": m.id, "sku": m.sku, "name": m.name,
                     "price": float(m.base_price or 0), "cost": float(m.base_cost or 0)}
                    for m in MenuItem.query.all()])

@admin_bp.route("/users", methods=["GET"])
@require_permission("users:read")
def list_users():
    from ..models.rbac import User
    return jsonify([u.to_dict() for u in User.query.all()])
"""

FILES[r"app\api\audit.py"] = """from flask import Blueprint, request, jsonify
from ..core.rbac import require_permission
from ..models.audit import AuditLog

audit_bp = Blueprint("audit", __name__)

@audit_bp.route("", methods=["GET"])
@require_permission("audit:read")
def list_audit():
    user_id = request.args.get("user_id", type=int)
    action = request.args.get("action")
    result = request.args.get("result")
    limit = min(request.args.get("limit", 100, type=int), 1000)
    q = AuditLog.query
    if user_id: q = q.filter_by(user_id=user_id)
    if action: q = q.filter_by(action=action)
    if result: q = q.filter_by(result=result)
    return jsonify([l.to_dict() for l in q.order_by(AuditLog.created_at.desc()).limit(limit).all()])
"""

FILES[r"app\api\export.py"] = """import io
import pandas as pd
from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import get_jwt_identity
from ..extensions import db
from ..core.rbac import require_permission
from ..models.reference import Restaurant, MenuItem, Customer
from ..models.integration import Recommendation, ExportLog
from ..models.rbac import User
from ..services.audit_service import log_action

export_bp = Blueprint("export", __name__)

REPORT_WHITELIST = {
    "locations":       lambda: [{"id": r.id, "code": r.code, "name": r.name, "city": r.city} for r in Restaurant.query.all()],
    "menu_items":      lambda: [{"id": m.id, "sku": m.sku, "name": m.name, "price": float(m.base_price or 0), "cost": float(m.base_cost or 0)} for m in MenuItem.query.all()],
    "customers":       lambda: [{"id": c.id, "external_id": c.external_id, "segment": c.segment} for c in Customer.query.all()],
    "recommendations": lambda: [{"id": r.id, "entity_type": r.entity_type, "entity_id": r.entity_id, "action": r.action, "priority": r.priority, "model_version": r.model_version} for r in Recommendation.query.all()],
}

@export_bp.route("/<report_name>", methods=["GET"])
@require_permission("export:csv")
def export_report(report_name):
    fmt = (request.args.get("format") or "csv").lower()
    if fmt not in ("csv", "xlsx"):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "format must be csv|xlsx"}}), 400
    if report_name not in REPORT_WHITELIST:
        return jsonify({"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Unknown report: {report_name}"}}), 404
    user = User.query.get(int(get_jwt_identity()))
    req_perm = "export:xlsx" if fmt == "xlsx" else "export:csv"
    if not user.has_permission(req_perm):
        return jsonify({"error": {"code": "RBAC_PERMISSION_DENIED", "message": f"Missing: {req_perm}"}}), 403
    rows = REPORT_WHITELIST[report_name]()
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    if fmt == "csv":
        df.to_csv(buf, index=False)
        mime, fname = "text/csv", f"{report_name}.csv"
    else:
        df.to_excel(buf, index=False, engine="openpyxl")
        mime, fname = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f"{report_name}.xlsx"
    buf.seek(0)
    log_action("EXPORT", f"export:{report_name}", "success", {"format": fmt, "rows": len(rows)})
    db.session.add(ExportLog(user_id=user.id, report_name=report_name, format=fmt, row_count=len(rows), status="success"))
    db.session.commit()
    return send_file(buf, mimetype=mime, as_attachment=True, download_name=fname)
"""

# --- إنشاء المجلدات والملفات ---
for rel_path, content in FILES.items():
    full = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  created: {rel_path}")

# إنشاء ملفات __init__.py الفارغة
for d in ["app", "app\\api", "app\\core", "app\\services", "app\\middleware", "app\\models", "tests"]:
    p = os.path.join(ROOT, d, "__init__.py")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").close()
        print(f"  created: {d}\\__init__.py")

print("\nDONE. All files created under", ROOT)
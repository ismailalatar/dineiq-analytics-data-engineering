from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, bcrypt, limiter
from sqlalchemy import text


def create_app(config_class=Config, overrides=None):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if overrides:
        app.config.update(overrides)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    from .api.auth import auth_bp
    from .api.admin import admin_bp
    from .api.audit import audit_bp
    from .api.export import export_bp
    from .api.models import models_bp

    app.register_blueprint(auth_bp,   url_prefix="/api/v1/auth")
    app.register_blueprint(admin_bp,  url_prefix="/api/v1")
    app.register_blueprint(audit_bp,  url_prefix="/api/v1/audit")
    app.register_blueprint(export_bp, url_prefix="/api/v1/export")
    app.register_blueprint(models_bp, url_prefix="/api/v1/models")

    from .core.errors import register_error_handlers
    register_error_handlers(app)

    from .middleware.audit import init_audit_middleware
    init_audit_middleware(app)

    @app.route("/health")
    def health():
        status = {"service": "DineIQ Backend", "status": "ok", "checks": {}}
        code = 200
        try:
            db.session.execute(text("SELECT 1"))
            status["checks"]["database"] = "ok"
        except Exception as e:
            status["checks"]["database"] = f"fail: {e}"
            status["status"] = "degraded"
            code = 503
        from .models.integration import ModelVersion
        try:
            n = ModelVersion.query.filter_by(is_active=True).count()
            status["checks"]["models"] = f"ok ({n} active)"
        except Exception:
            status["checks"]["models"] = "unavailable"
        return status, code

    return app
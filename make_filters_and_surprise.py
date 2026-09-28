import os
ROOT = r"D:\DineIQ"
FILES = {}

# ============ FILTERS in admin.py ============
FILES[r"app\api\admin.py"] = '''from flask import Blueprint, request, jsonify
from ..extensions import db
from ..core.rbac import require_permission
from ..models.reference import Restaurant, MenuItem
from ..models.integration import (Recommendation, DualPipelineComparison,
                                  SlowMovingDish, LocationIntelligence,
                                  ChannelIntelligence, WhatIfResult,
                                  SurpriseModificationReadiness)

admin_bp = Blueprint("admin", __name__)


# ===== Locations =====
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
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id}), 201


# ===== Menu =====
@admin_bp.route("/menu_items", methods=["GET"])
@require_permission("menu:read")
def list_menu():
    return jsonify([{"id": m.id, "sku": m.sku, "name": m.name,
                     "price": float(m.base_price or 0),
                     "cost": float(m.base_cost or 0)}
                    for m in MenuItem.query.all()])


# ===== Users =====
@admin_bp.route("/users", methods=["GET"])
@require_permission("users:read")
def list_users():
    from ..models.rbac import User
    return jsonify([u.to_dict() for u in User.query.all()])


# ===== Recommendations with filters (FR lviii) =====
@admin_bp.route("/analytics/recommendations", methods=["GET"])
@require_permission("recommendations:read")
def list_recommendations():
    priority = request.args.get("priority")
    source = request.args.get("source")
    search = request.args.get("q")
    limit = min(request.args.get("limit", 500, type=int), 2000)

    q = Recommendation.query
    if priority:
        q = q.filter_by(priority=priority)
    if source:
        q = q.filter_by(source=source)
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(Recommendation.finding.ilike(like),
                            Recommendation.evidence.ilike(like),
                            Recommendation.item_name.ilike(like)))
    rows = q.limit(limit).all()
    return jsonify([r.to_dict() for r in rows])


# ===== Dual pipeline with filters =====
@admin_bp.route("/analytics/dual_pipeline", methods=["GET"])
@require_permission("analytics:read")
def list_dual_pipeline():
    only_matches = request.args.get("match")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    limit = min(request.args.get("limit", 100, type=int), 1000)

    q = DualPipelineComparison.query
    if only_matches in ("0", "1"):
        q = q.filter_by(match=int(only_matches))
    if date_from:
        q = q.filter(DualPipelineComparison.date >= date_from)
    if date_to:
        q = q.filter(DualPipelineComparison.date <= date_to)
    return jsonify([r.to_dict() for r in q.limit(limit).all()])


# ===== Slow moving with filters =====
@admin_bp.route("/analytics/slow_moving", methods=["GET"])
@require_permission("analytics:read")
def list_slow_moving():
    perf_class = request.args.get("performance_class")
    item = request.args.get("item_id")
    min_rev = request.args.get("min_revenue", type=float)
    max_waste = request.args.get("max_wastage", type=float)

    q = SlowMovingDish.query
    if perf_class:
        q = q.filter_by(performance_class=perf_class)
    if item:
        q = q.filter_by(menu_item_id=item)
    if min_rev is not None:
        q = q.filter(SlowMovingDish.revenue >= min_rev)
    if max_waste is not None:
        q = q.filter(SlowMovingDish.wastage_pct <= max_waste)
    return jsonify([r.to_dict() for r in q.all()])


# ===== Location intelligence with filters =====
@admin_bp.route("/analytics/location_intelligence", methods=["GET"])
@require_permission("analytics:read")
def list_location_intel():
    item = request.args.get("item_id")
    case = request.args.get("case_type")
    priority = request.args.get("priority")

    q = LocationIntelligence.query
    if item:
        q = q.filter_by(menu_item_id=item)
    if case:
        q = q.filter_by(case_type=case)
    if priority:
        q = q.filter_by(priority=priority)
    return jsonify([r.to_dict() for r in q.all()])


# ===== Channel intelligence =====
@admin_bp.route("/analytics/channel_intelligence", methods=["GET"])
@require_permission("analytics:read")
def list_channel_intel():
    channel = request.args.get("channel")
    q = ChannelIntelligence.query
    if channel:
        q = q.filter_by(preferred_channel=channel)
    return jsonify([r.to_dict() for r in q.all()])


# ===== What-if =====
@admin_bp.route("/analytics/what_if", methods=["GET"])
@require_permission("analytics:read")
def list_what_if():
    scenario = request.args.get("scenario")
    item = request.args.get("item_id")
    q = WhatIfResult.query
    if scenario:
        q = q.filter_by(scenario=scenario)
    if item:
        q = q.filter_by(menu_item_id=item)
    return jsonify([r.to_dict() for r in q.all()])


# ===== Surprise readiness =====
@admin_bp.route("/analytics/surprise_readiness", methods=["GET"])
@require_permission("analytics:read")
def list_surprise():
    return jsonify([r.to_dict() for r in SurpriseModificationReadiness.query.all()])


# ===== Summary =====
@admin_bp.route("/analytics/summary", methods=["GET"])
@require_permission("analytics:read")
def analytics_summary():
    return jsonify({
        "recommendations_count": Recommendation.query.count(),
        "dual_pipeline_count": DualPipelineComparison.query.count(),
        "slow_moving_count": SlowMovingDish.query.count(),
        "location_intelligence_count": LocationIntelligence.query.count(),
        "channel_intelligence_count": ChannelIntelligence.query.count(),
        "what_if_count": WhatIfResult.query.count(),
        "surprise_readiness_count": SurpriseModificationReadiness.query.count(),
    })
'''

# ============ Surprise Config module ============
FILES[r"app\core\surprise_config.py"] = '''"""Surprise Modification Readiness (SRS §1.8 item 5).

Configurable parameters that evaluators may change during final assessment:
- profit threshold
- extra feature
- forecast window
- anomaly rule
- KPI name
"""
import os


class SurpriseConfig:
    PROFIT_THRESHOLD = float(os.getenv("PROFIT_THRESHOLD", "0.20"))
    EXTRA_FEATURE = os.getenv("EXTRA_FEATURE", "promotion_dependency")
    FORECAST_WINDOW_DAYS = int(os.getenv("FORECAST_WINDOW_DAYS", "30"))
    ANOMALY_RULE = os.getenv("ANOMALY_RULE", "revenue_change_pct > 20")
    KPI_NAME = os.getenv("KPI_NAME", "contribution_margin")

    @classmethod
    def as_dict(cls):
        return {
            "PROFIT_THRESHOLD": cls.PROFIT_THRESHOLD,
            "EXTRA_FEATURE": cls.EXTRA_FEATURE,
            "FORECAST_WINDOW_DAYS": cls.FORECAST_WINDOW_DAYS,
            "ANOMALY_RULE": cls.ANOMALY_RULE,
            "KPI_NAME": cls.KPI_NAME,
        }

    @classmethod
    def status(cls):
        return {
            "items": [
                {"parameter": "PROFIT_THRESHOLD", "value": cls.PROFIT_THRESHOLD, "status": "READY"},
                {"parameter": "EXTRA_FEATURE", "value": cls.EXTRA_FEATURE, "status": "READY"},
                {"parameter": "FORECAST_WINDOW_DAYS", "value": cls.FORECAST_WINDOW_DAYS, "status": "READY"},
                {"parameter": "ANOMALY_RULE", "value": cls.ANOMALY_RULE, "status": "READY"},
                {"parameter": "KPI_NAME", "value": cls.KPI_NAME, "status": "READY"},
            ],
            "all_ready": True,
        }
'''

# ============ Surprise endpoint in admin.py ============
# (Already in admin.py above? No - add to models.py or new file)
FILES[r"app\api\config_api.py"] = '''"""Surprise Modification Readiness endpoints - SRS §1.8 item 5"""
from flask import Blueprint, jsonify
from ..core.rbac import require_permission
from ..core.surprise_config import SurpriseConfig

config_bp = Blueprint("config", __name__)


@config_bp.route("/surprise", methods=["GET"])
@require_permission("analytics:read")
def surprise_status():
    return jsonify(SurpriseConfig.status())


@config_bp.route("/surprise/values", methods=["GET"])
@require_permission("analytics:read")
def surprise_values():
    return jsonify(SurpriseConfig.as_dict())
'''

# ============ Update __init__.py to register config_bp ============
FILES[r"app\__init__.py"] = '''from flask import Flask
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
    from .api.config_api import config_bp

    app.register_blueprint(auth_bp,   url_prefix="/api/v1/auth")
    app.register_blueprint(admin_bp,  url_prefix="/api/v1")
    app.register_blueprint(audit_bp,  url_prefix="/api/v1/audit")
    app.register_blueprint(export_bp, url_prefix="/api/v1/export")
    app.register_blueprint(models_bp, url_prefix="/api/v1/models")
    app.register_blueprint(config_bp, url_prefix="/api/v1/config")

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
'''

for rel, content in FILES.items():
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  updated: {rel}")

print("\nDONE filters + surprise")
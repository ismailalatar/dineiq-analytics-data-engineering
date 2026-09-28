from flask import Blueprint, request, jsonify
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


# ===== 4B outputs — read-only endpoints for 4C =====
@admin_bp.route("/analytics/recommendations", methods=["GET"])
@require_permission("recommendations:read")
def list_recommendations():
    return jsonify([r.to_dict() for r in Recommendation.query.all()])


@admin_bp.route("/analytics/dual_pipeline", methods=["GET"])
@require_permission("analytics:read")
def list_dual_pipeline():
    limit = min(request.args.get("limit", 100, type=int), 500)
    return jsonify([r.to_dict() for r in DualPipelineComparison.query.limit(limit).all()])


@admin_bp.route("/analytics/slow_moving", methods=["GET"])
@require_permission("analytics:read")
def list_slow_moving():
    return jsonify([r.to_dict() for r in SlowMovingDish.query.all()])


@admin_bp.route("/analytics/location_intelligence", methods=["GET"])
@require_permission("analytics:read")
def list_location_intel():
    return jsonify([r.to_dict() for r in LocationIntelligence.query.all()])


@admin_bp.route("/analytics/channel_intelligence", methods=["GET"])
@require_permission("analytics:read")
def list_channel_intel():
    return jsonify([r.to_dict() for r in ChannelIntelligence.query.all()])


@admin_bp.route("/analytics/what_if", methods=["GET"])
@require_permission("analytics:read")
def list_what_if():
    return jsonify([r.to_dict() for r in WhatIfResult.query.all()])


@admin_bp.route("/analytics/surprise_readiness", methods=["GET"])
@require_permission("analytics:read")
def list_surprise():
    return jsonify([r.to_dict() for r in SurpriseModificationReadiness.query.all()])


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
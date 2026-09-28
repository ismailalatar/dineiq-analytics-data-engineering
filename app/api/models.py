"""Model Version Tracking endpoints - SRS §1.6 FR lxii"""
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..core.rbac import require_permission
from ..models.integration import ModelVersion
from ..services.audit_service import log_action

models_bp = Blueprint("models", __name__)


@models_bp.route("", methods=["GET"])
@require_permission("models:read")
def list_models():
    pipeline = request.args.get("pipeline")
    q = ModelVersion.query
    if pipeline in ("spark", "python"):
        q = q.filter_by(pipeline=pipeline)
    rows = q.order_by(ModelVersion.trained_at.desc()).all()
    return jsonify([{
        "id": r.id, "name": r.name, "version": r.version,
        "pipeline": r.pipeline, "metrics": r.metrics_json,
        "trained_at": r.trained_at.isoformat() if r.trained_at else None,
        "is_active": r.is_active
    } for r in rows])


@models_bp.route("/active", methods=["GET"])
@require_permission("models:read")
def list_active():
    rows = ModelVersion.query.filter_by(is_active=True).all()
    return jsonify([{
        "id": r.id, "name": r.name, "version": r.version,
        "pipeline": r.pipeline, "metrics": r.metrics_json
    } for r in rows])


@models_bp.route("", methods=["POST"])
@require_permission("models:write")
def register_model():
    d = request.get_json() or {}
    required = ["name", "version", "pipeline"]
    missing = [k for k in required if not d.get(k)]
    if missing:
        return jsonify({"error": {"code": "VALIDATION_ERROR",
                                  "message": f"Missing: {missing}",
                                  "details": None}}), 400
    if d["pipeline"] not in ("spark", "python"):
        return jsonify({"error": {"code": "VALIDATION_ERROR",
                                  "message": "pipeline must be 'spark' or 'python'",
                                  "details": None}}), 400

    existing = ModelVersion.query.filter_by(
        name=d["name"], version=d["version"], pipeline=d["pipeline"]
    ).first()
    if existing:
        return jsonify({"error": {"code": "CONFLICT_DUPLICATE",
                                  "message": "Model version already exists",
                                  "details": {"id": existing.id}}}), 409

    import json
    mv = ModelVersion(
        name=d["name"][:80],
        version=d["version"][:40],
        pipeline=d["pipeline"],
        metrics_json=json.dumps(d.get("metrics", {})) if d.get("metrics") else None,
        is_active=bool(d.get("is_active", False)),
    )
    db.session.add(mv)
    db.session.commit()
    log_action("MODEL_REGISTERED", f"models:{mv.id}", "success",
               {"name": mv.name, "version": mv.version, "pipeline": mv.pipeline})
    return jsonify({"id": mv.id, "message": "Model version registered"}), 201


@models_bp.route("/<int:model_id>/activate", methods=["PATCH"])
@require_permission("models:write")
def activate(model_id):
    mv = db.session.get(ModelVersion, model_id)
    if not mv:
        return jsonify({"error": {"code": "RESOURCE_NOT_FOUND",
                                  "message": "Model version not found",
                                  "details": None}}), 404
    ModelVersion.query.filter_by(
        name=mv.name, pipeline=mv.pipeline
    ).update({"is_active": False})
    mv.is_active = True
    db.session.commit()
    log_action("MODEL_ACTIVATED", f"models:{mv.id}", "success",
               {"name": mv.name, "version": mv.version})
    return jsonify({"message": "Activated", "id": mv.id,
                    "name": mv.name, "version": mv.version})
"""Surprise Modification Readiness endpoints - SRS §1.8 item 5"""
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

from flask import Blueprint, request, jsonify
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

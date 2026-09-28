import io
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
    user = db.session.get(User, int(get_jwt_identity()))
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

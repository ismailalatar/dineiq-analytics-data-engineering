import io
import pandas as pd
from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import get_jwt_identity
from ..extensions import db
from ..core.rbac import require_permission
from ..models.rbac import User
from ..models.reference import Restaurant, MenuItem, Customer
from ..models.integration import (Recommendation, ExportLog,
                                  DualPipelineComparison, SlowMovingDish,
                                  LocationIntelligence, ChannelIntelligence,
                                  WhatIfResult, SurpriseModificationReadiness)
from ..services.audit_service import log_action

export_bp = Blueprint("export", __name__)


REPORT_WHITELIST = {
    "locations": lambda: [
        {"id": r.id, "code": r.code, "name": r.name, "city": r.city}
        for r in Restaurant.query.all()
    ],
    "menu_items": lambda: [
        {"id": m.id, "sku": m.sku, "name": m.name,
         "price": float(m.base_price or 0), "cost": float(m.base_cost or 0)}
        for m in MenuItem.query.all()
    ],
    "customers": lambda: [
        {"id": c.id, "external_id": c.external_id, "segment": c.segment}
        for c in Customer.query.all()
    ],
    "recommendations": lambda: [r.to_dict() for r in Recommendation.query.all()],
    "dual_pipeline": lambda: [r.to_dict() for r in DualPipelineComparison.query.all()],
    "slow_moving": lambda: [r.to_dict() for r in SlowMovingDish.query.all()],
    "location_intelligence": lambda: [r.to_dict() for r in LocationIntelligence.query.all()],
    "channel_intelligence": lambda: [r.to_dict() for r in ChannelIntelligence.query.all()],
    "what_if": lambda: [r.to_dict() for r in WhatIfResult.query.all()],
    "surprise_readiness": lambda: [r.to_dict() for r in SurpriseModificationReadiness.query.all()],
}


@export_bp.route("/<report_name>", methods=["GET"])
@require_permission("export:csv")
def export_report(report_name):
    fmt = (request.args.get("format") or "csv").lower()
    if fmt not in ("csv", "xlsx"):
        return jsonify({"error": {
            "code": "VALIDATION_ERROR",
            "message": "format must be csv or xlsx",
            "details": None
        }}), 400

    if report_name not in REPORT_WHITELIST:
        return jsonify({"error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": f"Unknown report: {report_name}",
            "details": {"allowed": sorted(REPORT_WHITELIST.keys())}
        }}), 404

    user = db.session.get(User, int(get_jwt_identity()))
    req_perm = "export:xlsx" if fmt == "xlsx" else "export:csv"
    if not user.has_permission(req_perm):
        return jsonify({"error": {
            "code": "RBAC_PERMISSION_DENIED",
            "message": f"Missing permission: {req_perm}",
            "details": None
        }}), 403

    rows = REPORT_WHITELIST[report_name]()
    df = pd.DataFrame(rows)

    buf = io.BytesIO()
    if fmt == "csv":
        df.to_csv(buf, index=False)
        mime = "text/csv"
        fname = f"{report_name}.csv"
    else:
        df.to_excel(buf, index=False, engine="openpyxl")
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = f"{report_name}.xlsx"
    buf.seek(0)

    log_action("EXPORT", f"export:{report_name}", "success",
               {"format": fmt, "rows": len(rows)})
    db.session.add(ExportLog(
        user_id=user.id, report_name=report_name,
        format=fmt, row_count=len(rows), status="success"
    ))
    db.session.commit()

    return send_file(buf, mimetype=mime, as_attachment=True, download_name=fname)
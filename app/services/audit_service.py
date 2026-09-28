import json
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

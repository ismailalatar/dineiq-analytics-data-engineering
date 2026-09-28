from datetime import datetime
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

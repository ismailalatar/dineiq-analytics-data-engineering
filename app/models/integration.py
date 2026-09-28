from datetime import datetime
from ..extensions import db

class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(40))
    entity_id = db.Column(db.String(60))
    action = db.Column(db.String(120))
    priority = db.Column(db.String(10))
    evidence_json = db.Column(db.Text, nullable=False)
    model_version = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ModelVersion(db.Model):
    __tablename__ = "model_versions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    version = db.Column(db.String(40), nullable=False)
    pipeline = db.Column(db.String(20))
    metrics_json = db.Column(db.Text)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)

class ExportLog(db.Model):
    __tablename__ = "export_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    report_name = db.Column(db.String(80))
    format = db.Column(db.String(10))
    row_count = db.Column(db.Integer)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

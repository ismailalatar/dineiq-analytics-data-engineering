from datetime import datetime
from ..extensions import db

class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id = db.Column(db.Integer, primary_key=True)
    finding = db.Column(db.String(200))
    evidence = db.Column(db.Text)
    action = db.Column(db.String(300))
    priority = db.Column(db.String(20))
    source = db.Column(db.String(80))
    menu_item_id = db.Column(db.String(40))
    item_name = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "finding": self.finding, "evidence": self.evidence,
                "action": self.action, "priority": self.priority,
                "source": self.source, "menu_item_id": self.menu_item_id,
                "item_name": self.item_name}

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

class DualPipelineComparison(db.Model):
    __tablename__ = "dual_pipeline_comparison"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    time_index = db.Column(db.Integer)
    actual = db.Column(db.Float)
    order_count = db.Column(db.Integer)
    python_prediction = db.Column(db.Float)
    spark_prediction = db.Column(db.Float)
    diff = db.Column(db.Float)
    error_pct = db.Column(db.Float)
    match = db.Column(db.Integer)
    explanation = db.Column(db.String(200))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != "id"} | {"id": self.id}

class SlowMovingDish(db.Model):
    __tablename__ = "slow_moving_dishes"
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.String(40), index=True)
    item_name = db.Column(db.String(150))
    category_name = db.Column(db.String(120))
    quantity_sold = db.Column(db.Float)
    revenue = db.Column(db.Float)
    profit_pct = db.Column(db.Float)
    wastage_pct = db.Column(db.Float)
    promotion_dependency = db.Column(db.Float)
    performance_class = db.Column(db.String(40))
    finding = db.Column(db.String(200))
    evidence = db.Column(db.Text)
    action = db.Column(db.String(300))
    priority = db.Column(db.String(20))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class LocationIntelligence(db.Model):
    __tablename__ = "location_intelligence"
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.String(40), index=True)
    item_name = db.Column(db.String(150))
    location_count = db.Column(db.Integer)
    max_location_quantity = db.Column(db.Float)
    min_location_quantity = db.Column(db.Float)
    location_gap = db.Column(db.Float)
    location_ratio = db.Column(db.Float)
    quantity_sold = db.Column(db.Float)
    revenue = db.Column(db.Float)
    case_type = db.Column(db.String(120))
    finding = db.Column(db.String(200))
    evidence = db.Column(db.Text)
    action = db.Column(db.String(300))
    priority = db.Column(db.String(20))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ChannelIntelligence(db.Model):
    __tablename__ = "channel_intelligence"
    id = db.Column(db.Integer, primary_key=True)
    preferred_channel = db.Column(db.String(60), unique=True, index=True)
    customers = db.Column(db.Integer)
    orders = db.Column(db.Integer)
    revenue = db.Column(db.Float)
    avg_order_value = db.Column(db.Float)
    avg_basket_size = db.Column(db.Float)
    avg_recency = db.Column(db.Float)
    finding = db.Column(db.String(200))
    evidence = db.Column(db.Text)
    action = db.Column(db.String(300))
    priority = db.Column(db.String(20))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class WhatIfResult(db.Model):
    __tablename__ = "what_if_results"
    id = db.Column(db.Integer, primary_key=True)
    scenario = db.Column(db.String(80))
    assumption = db.Column(db.Text)
    estimate_flag = db.Column(db.String(80))
    menu_item_id = db.Column(db.String(40))
    item_name = db.Column(db.String(150))
    baseline_demand = db.Column(db.Float)
    estimated_demand = db.Column(db.Float)
    baseline_revenue = db.Column(db.Float)
    estimated_revenue = db.Column(db.Float)
    baseline_contribution_margin = db.Column(db.Float)
    estimated_contribution_margin = db.Column(db.Float)
    baseline_wastage_pct = db.Column(db.Float)
    estimated_wastage_pct = db.Column(db.Float)
    baseline_profitability_pct = db.Column(db.Float)
    estimated_profitability_pct = db.Column(db.Float)
    revenue_change = db.Column(db.Float)
    contribution_margin_change = db.Column(db.Float)
    demand_change = db.Column(db.Float)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class SurpriseModificationReadiness(db.Model):
    __tablename__ = "surprise_modification_readiness"
    id = db.Column(db.Integer, primary_key=True)
    modification = db.Column(db.String(80))
    parameter = db.Column(db.String(80))
    current_value = db.Column(db.String(120))
    status = db.Column(db.String(20))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
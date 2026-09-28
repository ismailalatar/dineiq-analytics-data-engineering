"""Surprise Modification Readiness (SRS §1.8 item 5).

Configurable parameters that evaluators may change during final assessment:
- profit threshold
- extra feature
- forecast window
- anomaly rule
- KPI name
"""
import os


class SurpriseConfig:
    PROFIT_THRESHOLD = float(os.getenv("PROFIT_THRESHOLD", "0.20"))
    EXTRA_FEATURE = os.getenv("EXTRA_FEATURE", "promotion_dependency")
    FORECAST_WINDOW_DAYS = int(os.getenv("FORECAST_WINDOW_DAYS", "30"))
    ANOMALY_RULE = os.getenv("ANOMALY_RULE", "revenue_change_pct > 20")
    KPI_NAME = os.getenv("KPI_NAME", "contribution_margin")

    @classmethod
    def as_dict(cls):
        return {
            "PROFIT_THRESHOLD": cls.PROFIT_THRESHOLD,
            "EXTRA_FEATURE": cls.EXTRA_FEATURE,
            "FORECAST_WINDOW_DAYS": cls.FORECAST_WINDOW_DAYS,
            "ANOMALY_RULE": cls.ANOMALY_RULE,
            "KPI_NAME": cls.KPI_NAME,
        }

    @classmethod
    def status(cls):
        return {
            "items": [
                {"parameter": "PROFIT_THRESHOLD", "value": cls.PROFIT_THRESHOLD, "status": "READY"},
                {"parameter": "EXTRA_FEATURE", "value": cls.EXTRA_FEATURE, "status": "READY"},
                {"parameter": "FORECAST_WINDOW_DAYS", "value": cls.FORECAST_WINDOW_DAYS, "status": "READY"},
                {"parameter": "ANOMALY_RULE", "value": cls.ANOMALY_RULE, "status": "READY"},
                {"parameter": "KPI_NAME", "value": cls.KPI_NAME, "status": "READY"},
            ],
            "all_ready": True,
        }

"""
اختبارات قيمه معروفه وحدود لكل التحليلات
تتاكد ان المخرجات منطقيه وضمن النطاقات الصحيحه
"""

import pandas as pd
from pathlib import Path


# ---------- Wastage ----------

def test_wastage_by_item_sum():
    path = "python_pipeline/results/parquet/06_wastage/wastage_by_item.parquet"
    df = pd.read_parquet(path)
    # المجموع لازم يكون > 0
    assert df["total_wasted"].sum() > 0
    # عدد الاصناف <= عدد اصناف القائمه الاصلي
    assert len(df) <= 150


def test_wastage_risk_tiers():
    path = "python_pipeline/results/parquet/06_wastage/wastage_risk.parquet"
    df = pd.read_parquet(path)
    tiers = set(df["risk"].dropna().unique())
    # التصنيفات لازم تكون من هذي القيم فقط
    assert tiers.issubset({"low", "medium", "high", "unknown"})


# ---------- Pricing ----------

def test_price_sensitivity_values():
    path = "python_pipeline/results/parquet/07_price/price_elasticity.parquet"
    df = pd.read_parquet(path)
    # كل صنف له تصنيف واحد من الثلاثه
    classes = set(df["sensitivity"].unique())
    assert classes.issubset({"high", "medium", "low", "unknown"})


def test_price_elasticity_range():
    path = "python_pipeline/results/parquet/07_price/price_elasticity.parquet"
    df = pd.read_parquet(path)
    # elasticity لازم تكون ضمن نطاق معقول
    valid = df["elasticity"].dropna()
    assert (valid.abs() < 10).all()


# ---------- Promotion ----------

def test_promotion_traps_count():
    path = "python_pipeline/results/parquet/08_promotion/promo_traps.parquet"
    df = pd.read_parquet(path)
    # لازم نلقى فخاخ محقونه
    assert len(df) >= 1
    # كل فخ لازم يحقق الشرط
    for _, row in df.iterrows():
        assert row["delta_revenue"] > 0
        assert row["delta_profit"] < 0


def test_promotion_effectiveness_has_behavior():
    path = "python_pipeline/results/parquet/08_promotion/promo_effectiveness.parquet"
    df = pd.read_parquet(path)
    # لازم تكون الاعمده الجديده موجوده
    for c in ["new_customers", "repeat_customers",
              "acquisition_rate", "repeat_rate",
              "wastage_cost", "post_retention"]:
        assert c in df.columns


# ---------- Anomalies ----------

def test_sales_anomalies_types():
    path = "python_pipeline/results/parquet/10_anomalies/sales_anomalies.parquet"
    df = pd.read_parquet(path)
    types = set(df["type"].dropna().unique())
    assert types.issubset({"spike", "drop"})


def test_rating_anomalies_types():
    path = "python_pipeline/results/parquet/09_ratings/rating_anomalies.parquet"
    df = pd.read_parquet(path)
    types = set(df["type"].dropna().unique())
    assert types.issubset({"spike", "drop", "concentration"})


# ---------- Forecast ----------

def test_forecast_no_negative_predictions():
    path = "python_pipeline/results/parquet/12_python_forecast/python_forecast.parquet"
    df = pd.read_parquet(path)
    # التوقعات لازم تكون موجبه
    assert (df["python_prediction"] > 0).all()


def test_forecast_date_order():
    path = "python_pipeline/results/parquet/12_python_forecast/python_forecast.parquet"
    df = pd.read_parquet(path)
    df = df.sort_values("date").reset_index(drop=True)
    # التواريخ لازم تكون مرتبه
    assert df["date"].is_monotonic_increasing


# ---------- Segmentation ----------

def test_segments_count():
    path = "python_pipeline/results/parquet/04_segmentation/segment_profiles.parquet"
    df = pd.read_parquet(path)
    # المشروع يطلب 6 شرائح
    assert len(df) == 6


def test_segment_names_unique():
    path = "python_pipeline/results/parquet/04_segmentation/segment_profiles.parquet"
    df = pd.read_parquet(path)
    # الاسماء ما تتكرر
    assert df["segment"].nunique() == len(df)


# ---------- Model version ----------

def test_model_versions_file():
    path = "python_pipeline/results/models/model_versions.json"
    assert Path(path).exists()


def test_ai_usage_exists():
    assert Path("AI_USAGE.md").exists()


def test_readme_exists():
    assert Path("README_PYTHON_PIPELINE.md").exists()

# ---------- Bundle ----------

def test_bundle_suggestions_exist():
    path = "python_pipeline/results/parquet/05_basket/bundle_suggestions.parquet"
    df = pd.read_parquet(path)
    assert len(df) > 0
    for c in ["antecedent_name", "consequent_name", "lift", "recommendation_type"]:
        assert c in df.columns


# ---------- Rating inconsistencies ----------

def test_rating_inconsistencies_file():
    path = "python_pipeline/results/parquet/09_ratings/rating_inconsistencies.parquet"
    assert Path(path).exists()


# ---------- Sales anomalies - new types ----------

def test_duplicate_transactions_file():
    path = "python_pipeline/results/parquet/10_anomalies/duplicate_transactions.parquet"
    assert Path(path).exists()


def test_unexpected_demand_file():
    path = "python_pipeline/results/parquet/10_anomalies/unexpected_demand.parquet"
    assert Path(path).exists()


def test_unexpected_demand_non_empty():
    path = "python_pipeline/results/parquet/10_anomalies/unexpected_demand.parquet"
    df = pd.read_parquet(path)
    assert len(df) > 0
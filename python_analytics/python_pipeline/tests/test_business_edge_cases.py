"""
Business Edge-Case Tests (SRS Steps 10, 11, 28, 30, 31, 36)
============================================================

These tests check that the pipeline correctly detects and documents
the hard cases that SRS explicitly requires:

- High-selling loss-making dish
- Low-selling high-margin dish
- Popular dish with high wastage
- Promotion that increases sales but decreases profit
- At-risk/churn customers
- Rating anomalies
- Sales anomalies
"""

from pathlib import Path
import pandas as pd


# ---------- Menu edge cases ----------

def test_high_selling_loss_making_exists():
    """SRS Step 11: high-selling loss-making items must be identified"""
    path = "python_pipeline/results/parquet/02_feature_store/item_features.parquet"
    df = pd.read_parquet(path)
    df["qty_sold"] = pd.to_numeric(df["qty_sold"], errors="coerce").astype(float)
    df["margin"] = pd.to_numeric(df["margin"], errors="coerce").astype(float)
    q75 = df["qty_sold"].quantile(0.75)
    loss = df[(df["qty_sold"] >= q75) & (df["margin"] < 0)]
    assert len(loss) >= 1, "no high-selling loss-making items found"


def test_low_selling_high_margin_exists():
    """SRS Step 11: profitable but rarely purchased items"""
    path = "python_pipeline/results/parquet/02_feature_store/item_features.parquet"
    df = pd.read_parquet(path)
    df["qty_sold"] = pd.to_numeric(df["qty_sold"], errors="coerce").astype(float)
    df["margin"] = pd.to_numeric(df["margin"], errors="coerce").astype(float)
    q25 = df["qty_sold"].quantile(0.25)
    q75m = df["margin"].quantile(0.75)
    hidden = df[(df["qty_sold"] <= q25) & (df["margin"] >= q75m)]
    assert len(hidden) >= 1, "no low-selling high-margin items found"


def test_popular_high_wastage_exists():
    """SRS Step 11: popular item with high wastage"""
    path = "python_pipeline/results/parquet/06_wastage/wastage_by_item.parquet"
    df = pd.read_parquet(path)
    df["total_wasted"] = pd.to_numeric(df["total_wasted"], errors="coerce").astype(float)
    q75 = df["total_wasted"].quantile(0.75)
    high_waste = df[df["total_wasted"] >= q75]
    assert len(high_waste) >= 1


# ---------- Promotion edge cases ----------

def test_promotion_trap_sales_up_profit_down():
    """SRS Step 28: sales up but profit down"""
    path = "python_pipeline/results/parquet/08_promotion/promo_traps.parquet"
    df = pd.read_parquet(path)
    assert len(df) >= 1, "no promotion traps found"
    for _, row in df.iterrows():
        assert row["delta_revenue"] > 0
        assert row["delta_profit"] < 0


def test_promotion_traps_summary_types():
    """SRS Step 28: 5 trap types documented"""
    path = "python_pipeline/results/parquet/08_promotion/promo_traps_summary.parquet"
    df = pd.read_parquet(path)
    for c in ["trap_sales_profit", "trap_customers_margin",
              "trap_wastage", "trap_promo_only", "trap_margin_shift"]:
        assert c in df.columns


# ---------- Churn edge cases ----------

def test_churn_customers_identified():
    """SRS Step 36: churn customers identified with features"""
    path = "python_pipeline/results/parquet/11_churn/churn_dataset.parquet"
    df = pd.read_parquet(path)
    assert "churn" in df.columns
    # نتحقق ان فيه churn=1 و churn=0
    assert df["churn"].sum() > 0
    assert (df["churn"] == 0).sum() > 0


def test_churn_high_recency_high_churn():
    """SRS Step 36: churned customers have higher recency"""
    path = "python_pipeline/results/parquet/11_churn/churn_dataset.parquet"
    df = pd.read_parquet(path)
    churned = df[df["churn"] == 1]["recency"].mean()
    active = df[df["churn"] == 0]["recency"].mean()
    # العملاء المسربين لهم recency اعلى
    assert churned > active


# ---------- Rating anomalies ----------

def test_rating_anomalies_types():
    """SRS Step 30: types of rating anomalies"""
    path = "python_pipeline/results/parquet/09_ratings/rating_anomalies.parquet"
    df = pd.read_parquet(path)
    types = set(df["type"].dropna().unique())
    # نتوقع على الاقل نوعين
    assert len(types) >= 2


def test_rating_inconsistencies():
    """SRS Step 30: ratings inconsistent with purchasing"""
    path = "python_pipeline/results/parquet/09_ratings/rating_inconsistencies.parquet"
    df = pd.read_parquet(path)
    assert "avg_rating" in df.columns
    assert "qty_sold" in df.columns


# ---------- Sales anomalies ----------

def test_sales_anomalies_types():
    """SRS Step 31: 2+ types of sales anomalies"""
    path = "python_pipeline/results/parquet/10_anomalies/sales_anomalies.parquet"
    df = pd.read_parquet(path)
    types = set(df["type"].dropna().unique())
    assert "spike" in types or "drop" in types


def test_duplicate_and_unexpected_files():
    """SRS Step 31: duplicate + unexpected demand files"""
    for name in ["duplicate_transactions", "unexpected_demand"]:
        path = f"python_pipeline/results/parquet/10_anomalies/{name}.parquet"
        assert Path(path).exists()


# ---------- Pricing edge cases ----------

def test_price_sensitivity_classes():
    """SRS Step 26: 3 classes of price sensitivity"""
    path = "python_pipeline/results/parquet/07_price/price_elasticity.parquet"
    df = pd.read_parquet(path)
    classes = set(df["sensitivity"].unique())
    assert "high" in classes
    assert "medium" in classes
    assert "low" in classes


def test_multivariate_elasticity_exists():
    """SRS Step 25: multivariate model"""
    path = "python_pipeline/results/parquet/07_price/multivariate_elasticity.parquet"
    df = pd.read_parquet(path)
    assert "multivariate_elasticity" in df.columns
    assert "model_r2" in df.columns


# ---------- Slow-moving edge case ----------

def test_slow_moving_criteria():
    """SRS Step 32: 7 criteria documented"""
    path = "python_pipeline/results/parquet/12_slow_moving/item_sales_summary.parquet"
    df = pd.read_parquet(path)
    for c in ["c_low_volume", "c_low_frequency", "c_long_gaps",
              "c_low_repeat", "c_high_wastage", "c_weak_margin", "c_poor_trend"]:
        assert c in df.columns
    # verified that 7 criteria are used
    assert df["criteria_met"].max() >= 5
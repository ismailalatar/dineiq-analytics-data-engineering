from pathlib import Path
import pandas as pd


def test_metrics_exist():
    path = "python_pipeline/results/parquet/13_wastage_risk_model/metrics.parquet"
    assert Path(path).exists()


def test_two_models():
    path = "python_pipeline/results/parquet/13_wastage_risk_model/metrics.parquet"
    df = pd.read_parquet(path)
    assert len(df) == 2
    assert set(df["model"]) == {"logistic", "random_forest"}


def test_auc_reasonable():
    path = "python_pipeline/results/parquet/13_wastage_risk_model/metrics.parquet"
    df = pd.read_parquet(path)
    # AUC لازم يكون افضل من العشوائي
    assert (df["test_auc"] > 0.6).all()
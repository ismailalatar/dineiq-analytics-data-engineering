from pathlib import Path
import pandas as pd


def test_forecast_files_exist():
    base = "python_pipeline/results/parquet/14_forecast_demand"
    for name in ["forecast_item", "forecast_category", "forecast_location",
                 "metrics_item", "metrics_category", "metrics_location",
                 "forecast_summary"]:
        assert Path(f"{base}/{name}.parquet").exists()


def test_forecast_summary_has_models():
    path = "python_pipeline/results/parquet/14_forecast_demand/forecast_summary.parquet"
    df = pd.read_parquet(path)
    models = set(df["model"])
    assert "gradient_boosting" in models
    assert "naive_baseline" in models


def test_naive_has_positive_r2():
    path = "python_pipeline/results/parquet/14_forecast_demand/forecast_summary.parquet"
    df = pd.read_parquet(path)
    naive = df[df["model"] == "naive_baseline"]
    # ال naive لازم يكون R2 موجب في المتوسط
    assert naive["avg_r2"].mean() > 0
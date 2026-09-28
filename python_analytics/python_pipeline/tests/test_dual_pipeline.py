from pathlib import Path
import pandas as pd


def test_python_forecast_exists():
    path = "python_pipeline/results/parquet/12_python_forecast/python_forecast.parquet"
    assert Path(path).exists()


def test_forecast_has_100_rows():
    # SRS Step 14 يتطلب 100 حاله اختبار على الاقل
    path = "python_pipeline/results/parquet/12_python_forecast/python_forecast.parquet"
    df = pd.read_parquet(path)
    assert len(df) == 100


def test_forecast_columns():
    path = "python_pipeline/results/parquet/12_python_forecast/python_forecast.parquet"
    df = pd.read_parquet(path)
    for c in ["date", "actual_revenue", "python_prediction"]:
        assert c in df.columns


def test_comparison_exists():
    path = "python_pipeline/results/parquet/13_dual_comparison/dual_pipeline_comparison.parquet"
    assert Path(path).exists()


def test_comparison_has_100_rows():
    path = "python_pipeline/results/parquet/13_dual_comparison/dual_pipeline_comparison.parquet"
    df = pd.read_parquet(path)
    assert len(df) == 100


def test_comparison_has_explanation_column():
    # SRS Step 14 يتطلب explanation of disagreement
    path = "python_pipeline/results/parquet/13_dual_comparison/dual_pipeline_comparison.parquet"
    df = pd.read_parquet(path)
    assert "explanation" in df.columns
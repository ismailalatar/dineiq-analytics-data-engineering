from pathlib import Path
import pandas as pd


def test_churn_metrics_exist():
    path = "python_pipeline/results/parquet/11_churn/churn_metrics.parquet"
    assert Path(path).exists()


def test_three_models_trained():
    path = "python_pipeline/results/parquet/11_churn/churn_metrics.parquet"
    df = pd.read_parquet(path)
    assert len(df) == 3
    names = set(df["model"])
    assert names == {"logistic", "random_forest", "gradient_boosting"}


def test_temporal_split_sizes():
    path = "python_pipeline/results/parquet/11_churn/churn_metrics.parquet"
    df = pd.read_parquet(path)
    # كل cohort له حجم مستقل، لا نفرض نسبه معينه
    # المهم ان كل المجموعات غير فارغه وان الاجمالي ثابت
    assert (df["train_size"] > 0).all()
    assert (df["val_size"] > 0).all()
    assert (df["test_size"] > 0).all()
    total = df["train_size"] + df["val_size"] + df["test_size"]
    assert total.nunique() == 1


def test_split_method_is_temporal():
    path = "python_pipeline/results/parquet/11_churn/churn_metrics.parquet"
    df = pd.read_parquet(path)
    assert "split_method" in df.columns
    # نتحقق انه يبدا بـtemporal
    assert df["split_method"].str.startswith("temporal").all()
    # القيمه الدقيقه (feature cutoff cohorts)
    assert (df["split_method"] == "temporal_cohort_feature_cutoff").all()

def test_models_saved():
    from python_pipeline.config import MODELS_DIR
    for name in ["logistic", "random_forest", "gradient_boosting"]:
        assert (MODELS_DIR / f"churn_{name}.pkl").exists()


def test_sample_predictions_count():
    path = "python_pipeline/results/parquet/11_churn/churn_predictions_sample.parquet"
    df = pd.read_parquet(path)
    assert len(df) == 100
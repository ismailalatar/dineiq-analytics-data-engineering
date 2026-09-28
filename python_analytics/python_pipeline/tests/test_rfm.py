import pandas as pd


def test_rfm_file_exists():
    path = "python_pipeline/results/parquet/03_rfm/customer_rfm.parquet"
    df = pd.read_parquet(path)
    assert len(df) > 0


def test_rfm_scores_range():
    path = "python_pipeline/results/parquet/03_rfm/customer_rfm.parquet"
    df = pd.read_parquet(path)
    for c in ["r_score", "f_score", "m_score"]:
        assert df[c].between(1, 4).all()
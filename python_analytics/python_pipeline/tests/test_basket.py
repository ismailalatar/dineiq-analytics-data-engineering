import pandas as pd


def test_basket_rules_exist():
    path = "python_pipeline/results/parquet/05_basket/basket_rules.parquet"
    df = pd.read_parquet(path)
    assert len(df) > 0


def test_lift_above_threshold():
    path = "python_pipeline/results/parquet/05_basket/basket_rules.parquet"
    df = pd.read_parquet(path)
    assert (df["lift"] >= 1.2).all()


def test_no_self_rule():
    path = "python_pipeline/results/parquet/05_basket/basket_rules.parquet"
    df = pd.read_parquet(path)
    assert (df["antecedent"] != df["consequent"]).all()
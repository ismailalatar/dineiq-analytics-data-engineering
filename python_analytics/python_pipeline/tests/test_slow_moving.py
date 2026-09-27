from pathlib import Path
import pandas as pd


def test_slow_moving_file_exists():
    path = "python_pipeline/results/parquet/12_slow_moving/slow_moving_dishes.parquet"
    assert Path(path).exists()


def test_slow_moving_non_empty():
    path = "python_pipeline/results/parquet/12_slow_moving/slow_moving_dishes.parquet"
    df = pd.read_parquet(path)
    assert len(df) > 0


def test_slow_moving_has_flags():
    path = "python_pipeline/results/parquet/12_slow_moving/slow_moving_dishes.parquet"
    df = pd.read_parquet(path)
    # الاعمده الضروريه موجوده
    for c in ["menu_item_id", "qty_sold", "revenue", "margin", "is_slow_moving"]:
        assert c in df.columns
    # كل الصفوف مصنفه كبطيئه
    assert df["is_slow_moving"].all()


def test_slow_moving_below_median():
    path = "python_pipeline/results/parquet/12_slow_moving/item_sales_summary.parquet"
    df = pd.read_parquet(path)
    # الاصناف البطيئه لازم تكون كمياتها تحت المتوسط
    slow = df[df["is_slow_moving"] == True]
    non_slow = df[df["is_slow_moving"] == False]
    assert slow["qty_sold"].mean() < non_slow["qty_sold"].mean()
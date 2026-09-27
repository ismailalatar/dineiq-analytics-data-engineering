"""
نقارن توقعات python مع توقعات spark
نقرا ملف spark من مجلد external
وندمجه مع توقعاتنا في جدول واحد
ونحسب نسبه الاتفاق
المخرجات تروح لمجلد 13_dual_comparison
"""

from pathlib import Path

import pandas as pd

from python_pipeline.config import RESULTS_DIR
from python_pipeline.lib.io_helpers import save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


PY_PATH = (
    RESULTS_DIR / "parquet" / "12_python_forecast" / "python_forecast.parquet"
)
SPARK_PATH = (
    RESULTS_DIR.parent / "external" / "spark_forecast_results.parquet"
)

# عتبه المطابقه
MATCH_THRESHOLD = 0.10


def load_python():
    df = pd.read_parquet(PY_PATH)
    df["date"] = pd.to_datetime(df["date"])
    log.info(f"python forecast: {len(df)} صف")
    return df


def load_spark():
    if not SPARK_PATH.exists():
        log.warning(f"spark file not found: {SPARK_PATH}")
        return None

    df = pd.read_parquet(SPARK_PATH)
    df["date"] = pd.to_datetime(df["date"])
    log.info(f"spark forecast: {len(df)} صف")
    return df


def build_comparison(py_df, spark_df):
    # ننضم على التاريخ
    df = py_df.copy()
    df = df.rename(columns={"actual_revenue": "actual"})

    if spark_df is None:
        df["spark_prediction"] = None
    else:
        sp = spark_df[["date", "prediction"]].rename(
            columns={"prediction": "spark_prediction"}
        )
        df = df.merge(sp, on="date", how="left")

    df["diff"] = (df["spark_prediction"] - df["python_prediction"]).round(2)
    df["error_pct"] = (
        (df["diff"].abs() / df["actual"].replace(0, float("nan"))) * 100
    ).round(2)

    # المطابقه
    df["match"] = (
        (df["diff"].abs() / df["actual"].replace(0, float("nan")))
        < MATCH_THRESHOLD
    ).astype("Int64")

    # نص تفسيري لكل صف
    def explain(row):
        if pd.isna(row.get("spark_prediction")):
            return "spark pending"
        if row["match"] == 1:
            return "close prediction"
        # غير متطابق - نشرح الاتجاه
        if row["python_prediction"] > row["actual"] and row["spark_prediction"] > row["actual"]:
            return "both over-predicted"
        if row["python_prediction"] < row["actual"] and row["spark_prediction"] < row["actual"]:
            return "both under-predicted"
        if row["diff"] > 0:
            return "spark higher than python"
        return "python higher than spark"

    df["explanation"] = df.apply(explain, axis=1)

    return df


def build_summary(df):
    n_with_spark = int(df["spark_prediction"].notna().sum()) if "spark_prediction" in df else 0
    n_total = len(df)
    if n_with_spark > 0:
        agreement = float(df["match"].dropna().mean())
    else:
        agreement = None

    summary = {
        "n_cases_total": n_total,
        "n_cases_compared": n_with_spark,
        "agreement_rate": round(agreement, 4) if agreement is not None else None,
        "match_threshold": MATCH_THRESHOLD,
        "status": "compared" if n_with_spark > 0 else "pending_spark",
    }
    return pd.DataFrame([summary])


def run():
    log.info("نبدا dual comparison")
    py_df = load_python()
    spark_df = load_spark()

    comp = build_comparison(py_df, spark_df)
    save_stage(comp, "13_dual_comparison", "dual_pipeline_comparison.parquet")
    log.info(f"comparison rows: {len(comp)}")

    summary = build_summary(comp)
    save_stage(summary, "13_dual_comparison", "dual_pipeline_summary.parquet")
    log.info(f"summary: {summary.to_dict(orient='records')[0]}")

    log.info("خلصنا dual comparison")


if __name__ == "__main__":
    run()
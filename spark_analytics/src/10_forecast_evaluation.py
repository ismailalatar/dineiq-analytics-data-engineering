import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# Paths
# ============================================================

BASE = Path(r"D:\DineIQ")

FORECAST_PATH = (
    BASE
    / "spark_analytics"
    / "results"
    / "demand_forecast_spark.parquet"
)

OUTPUT_METRICS = (
    BASE
    / "spark_analytics"
    / "results"
    / "forecast_metrics.csv"
)

OUTPUT_JSON = (
    BASE
    / "spark_analytics"
    / "reports"
    / "forecast_metrics.json"
)


# ============================================================
# Load forecast
# ============================================================

df = pd.read_parquet(FORECAST_PATH)

df["date"] = pd.to_datetime(df["date"])

df["actual"] = pd.to_numeric(df["actual"], errors="coerce")
df["predicted"] = pd.to_numeric(df["predicted"], errors="coerce")

df = df.dropna(subset=["actual", "predicted"])

print("=" * 60)
print("DINEIQ - FORECAST EVALUATION")
print("=" * 60)

print("Rows:", len(df))
print("Items:", df["item_id"].nunique())
print(
    "Date range:",
    df["date"].min().date(),
    "to",
    df["date"].max().date(),
)


# ============================================================
# Model metrics
# ============================================================

y_true = df["actual"].to_numpy()
y_pred = df["predicted"].to_numpy()

mae = mean_absolute_error(y_true, y_pred)

rmse = np.sqrt(
    mean_squared_error(y_true, y_pred)
)

r2 = r2_score(y_true, y_pred)

# Avoid division by zero for MAPE
non_zero = y_true != 0

if non_zero.any():
    mape = (
        np.mean(
            np.abs(
                (y_true[non_zero] - y_pred[non_zero])
                / y_true[non_zero]
            )
        )
        * 100
    )
else:
    mape = np.nan


# ============================================================
# Naive baseline
#
# Baseline = previous observed value for the same item.
# This is created only from earlier observations.
# ============================================================

df = df.sort_values(
    ["item_id", "date"]
).copy()

df["baseline_prediction"] = (
    df.groupby("item_id")["actual"]
    .shift(1)
)

baseline = df.dropna(
    subset=["baseline_prediction"]
).copy()

baseline_true = baseline["actual"].to_numpy()
baseline_pred = baseline["baseline_prediction"].to_numpy()

baseline_mae = mean_absolute_error(
    baseline_true,
    baseline_pred,
)

baseline_rmse = np.sqrt(
    mean_squared_error(
        baseline_true,
        baseline_pred,
    )
)

baseline_r2 = r2_score(
    baseline_true,
    baseline_pred,
)

baseline_non_zero = baseline_true != 0

if baseline_non_zero.any():
    baseline_mape = (
        np.mean(
            np.abs(
                (
                    baseline_true[baseline_non_zero]
                    - baseline_pred[baseline_non_zero]
                )
                / baseline_true[baseline_non_zero]
            )
        )
        * 100
    )
else:
    baseline_mape = np.nan


# ============================================================
# Comparison
# ============================================================

results = pd.DataFrame(
    [
        {
            "model": "Spark Random Forest",
            "model_version": "v2.0",
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
            "R2": r2,
            "rows": len(df),
        },
        {
            "model": "Naive Previous Value Baseline",
            "model_version": "baseline-v1",
            "MAE": baseline_mae,
            "RMSE": baseline_rmse,
            "MAPE": baseline_mape,
            "R2": baseline_r2,
            "rows": len(baseline),
        },
    ]
)

print("\nEvaluation results:")
print(results.to_string(index=False))


# ============================================================
# Improvement check
# Lower MAE/RMSE/MAPE is better.
# Higher R2 is better.
# ============================================================

mae_improvement = (
    (baseline_mae - mae)
    / baseline_mae
    * 100
    if baseline_mae != 0
    else np.nan
)

rmse_improvement = (
    (baseline_rmse - rmse)
    / baseline_rmse
    * 100
    if baseline_rmse != 0
    else np.nan
)

mape_improvement = (
    (baseline_mape - mape)
    / baseline_mape
    * 100
    if baseline_mape != 0
    else np.nan
)

print("\nImprovement over baseline:")
print(f"MAE:  {mae_improvement:.2f}%")
print(f"RMSE: {rmse_improvement:.2f}%")
print(f"MAPE: {mape_improvement:.2f}%")

model_beats_baseline = (
    mae < baseline_mae
    and rmse < baseline_rmse
)

print(
    "\nModel beats baseline:",
    model_beats_baseline,
)


# ============================================================
# Save metrics
# ============================================================

OUTPUT_METRICS.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_JSON.parent.mkdir(
    parents=True,
    exist_ok=True,
)

results.to_csv(
    OUTPUT_METRICS,
    index=False,
)

summary = {
    "model": "Spark Random Forest",
    "model_version": "v2.0",
    "forecast_rows": int(len(df)),
    "items": int(df["item_id"].nunique()),
    "metrics": {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "MAPE": float(mape),
        "R2": float(r2),
    },
    "baseline": {
        "model": "Naive Previous Value",
        "version": "baseline-v1",
        "MAE": float(baseline_mae),
        "RMSE": float(baseline_rmse),
        "MAPE": float(baseline_mape),
        "R2": float(baseline_r2),
    },
    "improvement_percent": {
        "MAE": float(mae_improvement),
        "RMSE": float(rmse_improvement),
        "MAPE": float(mape_improvement),
    },
    "beats_baseline": bool(model_beats_baseline),
}

with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        summary,
        f,
        indent=4,
    )

print("\nSaved:")
print(OUTPUT_METRICS)
print(OUTPUT_JSON)

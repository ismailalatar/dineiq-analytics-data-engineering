"""
Demand Forecasting — Extended Feature Set
==========================================

Features (all from past only):
- Lag 1, 7, 14, 28
- Rolling Mean 7, 14, 28
- Rolling Std 7, 28
- Day of week, weekend, month, week of year
- Location, item, category (implicit in entity grouping)

Models compared:
- Naive baseline (lag_1)
- Moving Average (rolling_mean_7)
- Linear Regression
- Gradient Boosting

Evaluation: MAE, RMSE, MAPE, R2
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from python_pipeline.config import RANDOM_SEED
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)

N_TEST_DAYS = 73
LAG_DAYS = [1, 7, 14, 28]
ROLLING_WINDOWS = [7, 14, 28]


def load_sales():
    o = load_clean_table("Orders")
    i = load_clean_table("Order_Items")
    menu = load_clean_table("Menu_Items")

    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o = o[o["order_status"] == "completed"].copy()
    o["date"] = o["order_timestamp"].dt.normalize()

    i["quantity"] = pd.to_numeric(i["quantity"], errors="coerce").fillna(0)

    m = i.merge(o[["order_id", "date", "restaurant_id"]], on="order_id", how="inner")
    m = m.merge(menu[["menu_item_id", "category_id"]], on="menu_item_id", how="left")
    return m


def aggregate_daily(m, level):
    if level == "item":
        key = "menu_item_id"
    elif level == "category":
        key = "category_id"
    elif level == "location":
        key = "restaurant_id"
    else:
        raise ValueError(f"unknown level {level}")

    g = m.groupby([key, "date"]).agg(qty=("quantity", "sum")).reset_index()
    g = g.rename(columns={key: "entity_id"})
    g = g.sort_values(["entity_id", "date"]).reset_index(drop=True)
    g["qty"] = g["qty"].astype(float)
    return g


def add_features(g):
    g = g.copy()
    g["time_index"] = g.groupby("entity_id").cumcount() + 1

    # calendar
    g["dow"] = g["date"].dt.dayofweek
    g["is_weekend"] = (g["dow"] >= 5).astype(int)
    g["month"] = g["date"].dt.month
    g["week_of_year"] = g["date"].dt.isocalendar().week.astype(int)

    # lag features
    for lag in LAG_DAYS:
        g[f"lag_{lag}"] = g.groupby("entity_id")["qty"].shift(lag)

    # rolling features
    for w in ROLLING_WINDOWS:
        g[f"rolling_mean_{w}"] = g.groupby("entity_id")["qty"].transform(
            lambda s: s.shift(1).rolling(w, min_periods=1).mean()
        )
    for w in [7, 28]:
        g[f"rolling_std_{w}"] = g.groupby("entity_id")["qty"].transform(
            lambda s: s.shift(1).rolling(w, min_periods=1).std()
        )

    return g


def compute_metrics(actual, pred):
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mask = ~np.isnan(pred)
    actual = actual[mask]
    pred = pred[mask]

    if len(actual) == 0:
        return {"mae": None, "rmse": None, "mape": None, "r2": None}

    mae = mean_absolute_error(actual, pred)
    rmse = mean_squared_error(actual, pred) ** 0.5
    mask2 = actual > 0
    mape = (abs(actual[mask2] - pred[mask2]) / actual[mask2]).mean() * 100 if mask2.any() else None
    try:
        r2 = r2_score(actual, pred)
    except Exception:
        r2 = None

    return {
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "mape": round(float(mape), 2) if mape is not None else None,
        "r2": round(float(r2), 4) if r2 is not None else None,
    }


def forecast_level(m, level, n_test=N_TEST_DAYS):
    log.info(f"forecasting level: {level}")
    g = aggregate_daily(m, level)
    g = add_features(g)

    feat_cols = (
        ["time_index", "dow", "is_weekend", "month", "week_of_year"]
        + [f"lag_{l}" for l in LAG_DAYS]
        + [f"rolling_mean_{w}" for w in ROLLING_WINDOWS]
        + [f"rolling_std_{w}" for w in [7, 28]]
    )

    rows = []
    all_metrics = []

    for entity, sub in g.groupby("entity_id"):
        sub = sub.dropna(subset=["lag_1", "qty"]).copy()
        if len(sub) < n_test + 20:
            continue

        train = sub.iloc[:-n_test]
        test = sub.iloc[-n_test:]

        y_train = train["qty"].values.astype(float)
        y_test = test["qty"].values.astype(float)

        # 1. naive baseline: lag_1
        pred_naive = test["lag_1"].values.astype(float)

        # 2. moving average: rolling_mean_7
        pred_ma = test["rolling_mean_7"].values.astype(float)

        # 3. linear regression
        X_train_lr = train[["time_index"]].values
        X_test_lr = test[["time_index"]].values
        lr = LinearRegression().fit(X_train_lr, y_train)
        pred_lr = np.clip(lr.predict(X_test_lr), 0, None)

        # 4. gradient boosting (full features)
        X_train_gb = train[feat_cols].fillna(0).values
        X_test_gb = test[feat_cols].fillna(0).values
        gb = GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            random_state=RANDOM_SEED
        ).fit(X_train_gb, y_train)
        pred_gb = np.clip(gb.predict(X_test_gb), 0, None)

        # حفظ التنبؤات
        for (_, trow), pn, pm, pl, pg in zip(
            test.iterrows(), pred_naive, pred_ma, pred_lr, pred_gb
        ):
            rows.append({
                "entity_id": entity,
                "date": trow["date"],
                "actual_qty": float(trow["qty"]),
                "pred_naive": round(float(pn), 4) if not np.isnan(pn) else None,
                "pred_moving_avg": round(float(pm), 4) if not np.isnan(pm) else None,
                "pred_linear": round(float(pl), 4),
                "pred_gradient_boosting": round(float(pg), 4),
            })

        # metrics
        for name, pred in [
            ("naive_baseline", pred_naive),
            ("moving_average", pred_ma),
            ("linear_regression", pred_lr),
            ("gradient_boosting", pred_gb),
        ]:
            met = compute_metrics(y_test, pred)
            met["entity_id"] = entity
            met["model"] = name
            all_metrics.append(met)

    return pd.DataFrame(rows), pd.DataFrame(all_metrics)


def run():
    log.info("Starting demand forecast")
    m = load_sales()
    log.info(f"sales rows: {len(m):,}")

    summary_rows = []

    for level in ["item", "category", "location"]:
        preds, metrics = forecast_level(m, level)
        if len(preds) == 0:
            log.warning(f"no predictions for {level}")
            continue

        save_stage(preds, "14_forecast_demand", f"forecast_{level}.parquet")
        save_stage(metrics, "14_forecast_demand", f"metrics_{level}.parquet")

        for model_name in metrics["model"].unique():
            sub = metrics[metrics["model"] == model_name]
            avg = {
                "level": level,
                "model": model_name,
                "n_entities": int(sub["entity_id"].nunique()),
                "avg_mae": round(sub["mae"].dropna().mean(), 2),
                "avg_rmse": round(sub["rmse"].dropna().mean(), 2),
                "avg_mape": round(sub["mape"].dropna().mean(), 2) if not sub["mape"].isna().all() else None,
                "avg_r2": round(sub["r2"].dropna().mean(), 4) if not sub["r2"].isna().all() else None,
            }
            summary_rows.append(avg)
            log.info(f"  {level} / {model_name}: mae={avg['avg_mae']}, r2={avg['avg_r2']}")

    summary = pd.DataFrame(summary_rows)
    save_stage(summary, "14_forecast_demand", "forecast_summary.parquet")
    log.info(f"\n{summary.to_string(index=False)}")
    log.info("Demand forecast done")


if __name__ == "__main__":
    run()
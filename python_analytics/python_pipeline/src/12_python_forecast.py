"""
نبني نموذج forecasting مستقل في python
نطبق فلتر الrevenue الموحد حسب قرار الطالب 1
revenue = SUM(line_total) مع استبعاد الانوماليات
نستخدم time_index كميزه وحيده زي الطالب 2
نقسم زمني - تدريب 293 يوم واختبار 73 يوم
المخرجات تروح لمجلد 12_python_forecast
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


# نسبه التقسيم - 266 تدريب و 100 اختبار حسب SRS Step 14
# (يجب أن يطابق الطالب 2 نفس التقسيم)
N_TRAIN = 266
N_TEST = 100


def load_daily_revenue():
    # نطبق الفلتر الموحد حسب قرار الطالب 1
    # revenue من line_total مع استبعاد الانوماليات
    o = load_clean_table("Orders")
    i = load_clean_table("Order_Items")

    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["date"] = o["order_timestamp"].dt.normalize()

    # انواع رقميه
    i["quantity"] = pd.to_numeric(i["quantity"], errors="coerce")
    i["unit_price"] = pd.to_numeric(i["unit_price"], errors="coerce")
    i["line_total"] = pd.to_numeric(i["line_total"], errors="coerce")

    # ندمج الطلبات مع الاسطر
    merged = i.merge(
        o[["order_id", "order_status", "date"]],
        on="order_id",
        how="inner",
    )

    # الفلتر الموحد حسب قرار الطالب 1
    valid = (
        (merged["order_status"] == "completed")
        & (merged["quantity"] > 0)
        & (merged["unit_price"] > 0)
        & (merged["line_total"] >= 0)
    )
    cleaned = merged[valid].copy()

    log.info(f"valid rows: {len(cleaned):,} / {len(merged):,}")

    daily = cleaned.groupby("date").agg(
        revenue=("line_total", "sum"),
        order_count=("order_id", "nunique"),
    ).reset_index().sort_values("date").reset_index(drop=True)

    # time index زي الطالب 2
    daily["time_index"] = range(1, len(daily) + 1)
    log.info(f"daily rows: {len(daily)}")
    return daily


def split_chrono(daily):
    # نقسم زمني بدون random
    train = daily.iloc[:N_TRAIN].copy()
    test = daily.iloc[N_TRAIN:N_TRAIN + N_TEST].copy()
    log.info(f"train: {len(train)} | test: {len(test)}")
    log.info(f"train end: {train['date'].max().date()}")
    log.info(f"test start: {test['date'].min().date()}")
    log.info(f"test end: {test['date'].max().date()}")
    return train, test


def train_python_model(train, test):
    # نموذج خطي بميزه time_index فقط
    X_train = train[["time_index"]].values
    y_train = train["revenue"].values.astype(float)
    X_test = test[["time_index"]].values

    model = LinearRegression()
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    return model, pred


def compute_metrics(actual, pred):
    mae = mean_absolute_error(actual, pred)
    rmse = mean_squared_error(actual, pred) ** 0.5
    mask = actual > 0
    mape = (abs(actual[mask] - pred[mask]) / actual[mask]).mean() * 100
    return {
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "mape": round(float(mape), 2),
    }


def run():
    log.info("نبدا python forecast")
    daily = load_daily_revenue()
    train, test = split_chrono(daily)

    model, py_pred = train_python_model(train, test)
    log.info(f"coef: {model.coef_[0]:.4f} | intercept: {model.intercept_:.2f}")

    m = compute_metrics(test["revenue"].values.astype(float), py_pred)
    log.info(f"metrics: {m}")

    # نحفظ التوقعات
    out = test[["date", "time_index", "revenue", "order_count"]].copy()
    out = out.rename(columns={"revenue": "actual_revenue"})
    out["python_prediction"] = py_pred.round(2)
    save_stage(out, "12_python_forecast", "python_forecast.parquet")

    # metrics
    save_stage(pd.DataFrame([m]), "12_python_forecast", "python_metrics.parquet")

    # ملخص الاعدادات
    summary = pd.DataFrame([{
        "n_train": len(train),
        "n_test": len(test),
        "train_start": str(train["date"].min().date()),
        "train_end": str(train["date"].max().date()),
        "test_start": str(test["date"].min().date()),
        "test_end": str(test["date"].max().date()),
        "feature": "time_index",
        "model": "LinearRegression",
        "revenue_definition": "SUM(line_total) with unified filter",
        "mae": m["mae"],
        "rmse": m["rmse"],
        "mape": m["mape"],
    }])
    save_stage(summary, "12_python_forecast", "python_summary.parquet")

    log.info("خلصنا python forecast")


if __name__ == "__main__":
    run()
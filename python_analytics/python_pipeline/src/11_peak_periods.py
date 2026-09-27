"""
نحلل فترات الذروه حسب SRS Step 19
الساعات والايام ونهايات الاسبوع والشهور والمواسم
والمواقع وقنوات الطلب
المخرجات تروح لمجلد 11_peak_periods
"""

import pandas as pd

from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_orders():
    o = load_clean_table("Orders")
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["hour"] = o["order_timestamp"].dt.hour
    o["dow"] = o["order_timestamp"].dt.day_name()
    o["month"] = o["order_timestamp"].dt.month
    o["weekend"] = o["order_timestamp"].dt.dayofweek >= 5
    o["total_amount"] = pd.to_numeric(o["total_amount"], errors="coerce").fillna(0)
    return o


def by_hour(o):
    # ذروه الساعات
    return o.groupby("hour").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2})


def by_day(o):
    # ذروه الايام
    return o.groupby("dow").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2})


def by_weekend(o):
    # نهايات الاسبوع
    return o.groupby("weekend").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2})


def by_month(o):
    # الشهور والمواسم
    return o.groupby("month").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2})


def by_location(o):
    # المواقع
    return o.groupby("restaurant_id").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2}).sort_values("revenue", ascending=False)


def by_location_hour(o):
    # المواقع × الساعات
    return o.groupby(["restaurant_id", "hour"]).agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2})


def by_channel(o):
    # قنوات الطلب
    return o.groupby("order_channel").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2})


def by_channel_hour(o):
    # قنوات الطلب × الساعات
    return o.groupby(["order_channel", "hour"]).agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().round({"revenue": 2})


def run():
    log.info("نبدا peak periods")
    o = load_orders()
    log.info(f"orders: {len(o):,}")

    save_stage(by_hour(o),         "11_peak_periods", "peaks_by_hour.parquet")
    save_stage(by_day(o),          "11_peak_periods", "peaks_by_day.parquet")
    save_stage(by_weekend(o),      "11_peak_periods", "peaks_by_weekend.parquet")
    save_stage(by_month(o),        "11_peak_periods", "peaks_by_month.parquet")
    save_stage(by_location(o),     "11_peak_periods", "peaks_by_location.parquet")
    save_stage(by_location_hour(o), "11_peak_periods", "peaks_location_hour.parquet")
    save_stage(by_channel(o),      "11_peak_periods", "peaks_by_channel.parquet")
    save_stage(by_channel_hour(o), "11_peak_periods", "peaks_channel_hour.parquet")

    # نضيف ملخص بأهم القمم
    summary = pd.DataFrame([{
        "peak_hour": int(by_hour(o).sort_values("orders", ascending=False).iloc[0]["hour"]),
        "peak_day": by_day(o).sort_values("orders", ascending=False).iloc[0]["dow"],
        "peak_month": int(by_month(o).sort_values("orders", ascending=False).iloc[0]["month"]),
        "peak_channel": by_channel(o).sort_values("orders", ascending=False).iloc[0]["order_channel"],
        "peak_location": int(by_location(o).iloc[0]["restaurant_id"]),
    }])
    save_stage(summary, "11_peak_periods", "peaks_summary.parquet")
    log.info(f"\nملخص القمم:\n{summary.to_string(index=False)}")
    log.info("خلصنا peak periods")


if __name__ == "__main__":
    run()
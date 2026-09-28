"""
نكشف الشذوذات في المبيعات حسب SRS Step 31
ارتفاعات وانخفاضات غير طبيعيه
قيم طلبات غريبه وخصومات غير معتاده
طلب غير متوقع و معاملات مكرره
المخرجات تروح لمجلد 10_anomalies
"""

import pandas as pd

from python_pipeline.config import (
    SALES_SPIKE_MULT,
    SALES_DROP_MULT,
    Z_THRESHOLD,
)
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load():
    o = load_clean_table("Orders")
    i = load_clean_table("Order_Items")

    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["total_amount"] = pd.to_numeric(o["total_amount"], errors="coerce").astype(float)
    o["subtotal"] = pd.to_numeric(o["subtotal"], errors="coerce").astype(float)
    o["discount_total"] = pd.to_numeric(o["discount_total"], errors="coerce").astype(float)

    o["date"] = o["order_timestamp"].dt.normalize()
    o["hour"] = o["order_timestamp"].dt.hour
    o["dow"] = o["order_timestamp"].dt.day_name()

    i["quantity"] = pd.to_numeric(i["quantity"], errors="coerce").astype(float)
    i["line_total"] = pd.to_numeric(i["line_total"], errors="coerce").astype(float)

    return o, i


def daily_sales_per_item(o, i):
    # مبيعات يوميه لكل صنف
    m = i.merge(o[["order_id", "date"]], on="order_id", how="inner")
    daily = m.groupby(["menu_item_id", "date"]).agg(
        qty=("quantity", "sum"),
        revenue=("line_total", "sum"),
    ).reset_index()
    daily["qty"] = daily["qty"].astype(float)
    return daily


def detect_sales_anomalies(daily):
    # نحسب z و mean لكل صنف
    stats = daily.groupby("menu_item_id")["qty"].agg(["mean", "std"]).reset_index()
    stats["mean"] = stats["mean"].astype(float)
    stats["std"] = stats["std"].astype(float)

    daily = daily.merge(stats, on="menu_item_id", how="left")
    daily["qty"] = daily["qty"].astype(float)
    daily["mean"] = daily["mean"].astype(float)
    daily["std"] = daily["std"].astype(float)
    daily["z"] = (daily["qty"] - daily["mean"]) / daily["std"].replace(0, float("nan"))

    daily["type"] = None

    # ارتفاع
    mask_spike = (daily["qty"] > SALES_SPIKE_MULT * daily["mean"]) | (daily["z"] > Z_THRESHOLD)
    daily.loc[mask_spike, "type"] = "spike"

    # انخفاض
    mask_drop = (
        (daily["qty"] > 0)
        & (daily["qty"] < SALES_DROP_MULT * daily["mean"])
        & daily["type"].isna()
    )
    daily.loc[mask_drop, "type"] = "drop"

    return daily[daily["type"].notna()].copy()


def order_value_anomalies(o):
    # قيم الطلبات الغريبه باستخدام iqr
    q1 = o["total_amount"].quantile(0.25)
    q3 = o["total_amount"].quantile(0.75)
    iqr = q3 - q1
    low = q1 - 3 * iqr
    high = q3 + 3 * iqr

    an = o[(o["total_amount"] < low) | (o["total_amount"] > high)].copy()
    an["type"] = "order_value"
    return an[["order_id", "customer_id", "restaurant_id",
               "order_timestamp", "total_amount", "type"]]


def discount_anomalies(o):
    # الخصومات الغريبه
    o2 = o.copy()
    o2["discount_pct"] = (
        o2["discount_total"] / o2["subtotal"].replace(0, float("nan"))
    ).fillna(0)

    mean = o2["discount_pct"].mean()
    std = o2["discount_pct"].std()

    an = o2[o2["discount_pct"] > (mean + 3 * std)].copy()
    an["type"] = "discount"
    return an[["order_id", "customer_id", "restaurant_id",
               "order_timestamp", "subtotal", "discount_total",
               "discount_pct", "type"]]


def duplicate_transactions(o, i):
    # نكشف الطلبات المكرره حسب:
    # نفس العميل + نفس المطعم + نفس التاريخ + نفس المبلغ
    # في نافذه 60 دقيقه
    o2 = o.copy().sort_values("order_timestamp")

    # نجمّع حسب المفتاح
    dup = o2.duplicated(
        subset=["customer_id", "restaurant_id", "total_amount"],
        keep=False
    )
    candidates = o2[dup].copy()

    # نتأكد انها في نفس اليوم وفي غضون ساعه
    candidates = candidates.sort_values(["customer_id", "order_timestamp"])
    candidates["prev_time"] = candidates.groupby(
        ["customer_id", "restaurant_id", "total_amount"]
    )["order_timestamp"].shift(1)
    candidates["time_gap_min"] = (
        (candidates["order_timestamp"] - candidates["prev_time"])
        .dt.total_seconds() / 60
    )

    # نعتبره مكرر اذا الفرق اقل من 60 دقيقه
    dups = candidates[candidates["time_gap_min"] < 60].copy()
    dups["type"] = "duplicate_transaction"
    return dups[[
        "order_id", "customer_id", "restaurant_id",
        "order_timestamp", "total_amount", "time_gap_min", "type"
    ]]


def unexpected_demand(o, i):
    # الطلب الغير متوقع: مزيج من صنفين نادرين في نفس الطلب
    # نستخدم عدد الاصناف المختلفه: طلبات بعدد اصناف > 3 اضعاف المتوسط
    items_per_order = i.groupby("order_id")["menu_item_id"].nunique()
    mean_items = items_per_order.mean()
    std_items = items_per_order.std()

    threshold = mean_items + 3 * std_items

    big_orders = items_per_order[items_per_order > threshold].reset_index()
    big_orders.columns = ["order_id", "n_items"]

    merged = big_orders.merge(
        o[["order_id", "customer_id", "restaurant_id", "order_timestamp", "total_amount"]],
        on="order_id", how="left"
    )
    merged["mean_items"] = round(mean_items, 2)
    merged["type"] = "unexpected_demand"
    return merged


def run():
    log.info("نبدا sales anomalies")
    o, i = load()

    daily = daily_sales_per_item(o, i)
    sales_an = detect_sales_anomalies(daily)
    save_stage(sales_an, "10_anomalies", "sales_anomalies.parquet")

    val_an = order_value_anomalies(o)
    save_stage(val_an, "10_anomalies", "order_value_anomalies.parquet")

    disc_an = discount_anomalies(o)
    save_stage(disc_an, "10_anomalies", "discount_anomalies.parquet")

    # جديد: معاملات مكرره
    dup_an = duplicate_transactions(o, i)
    save_stage(dup_an, "10_anomalies", "duplicate_transactions.parquet")

    # جديد: طلب غير متوقع
    unex_an = unexpected_demand(o, i)
    save_stage(unex_an, "10_anomalies", "unexpected_demand.parquet")

    log.info("خلصنا")
    log.info(f"sales anomalies: {len(sales_an):,}")
    log.info(f"order value anomalies: {len(val_an):,}")
    log.info(f"discount anomalies: {len(disc_an):,}")
    log.info(f"duplicate transactions: {len(dup_an):,}")
    log.info(f"unexpected demand: {len(unex_an):,}")
    if len(sales_an):
        log.info(f"\n{sales_an['type'].value_counts().to_string()}")


if __name__ == "__main__":
    run()
    
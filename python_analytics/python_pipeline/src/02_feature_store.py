"""
نبني الميزات المشتركه الي راح نستخدمها في كل التحليلات
كل الميزات نحسبها من window محدده عشان نمنع التسريب
المخرجات تروح لمجلد 02_feature_store
"""

import pandas as pd

from python_pipeline.config import FEATURE_WINDOW_END
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_sources():
    # الجداول الي نحتاجها
    return {
        "orders": load_clean_table("Orders"),
        "items": load_clean_table("Order_Items"),
        "customers": load_clean_table("Customers"),
        "menu": load_clean_table("Menu_Items"),
    }


def clean_orders(orders):
    # نحوّل التاريخ ونستبعد الملغاة
    orders = orders.copy()
    orders["order_timestamp"] = pd.to_datetime(orders["order_timestamp"])
    orders = orders[orders["order_status"] != "cancelled"]
    return orders


def filter_features_window(orders):
    # نقطع الميزات عند نهايه النافذه
    cutoff = pd.Timestamp(FEATURE_WINDOW_END) + pd.Timedelta(days=1)
    return orders[orders["order_timestamp"] < cutoff].copy()


def build_customer_features(orders, items):
    # ننضم الطلبات مع التفاصيل
    joined = items.merge(
        orders[["order_id", "customer_id", "order_timestamp"]],
        on="order_id",
        how="inner",
    )

    # الميزات الاساسيه لكل عميل
    feats = joined.groupby("customer_id").agg(
        last_order=("order_timestamp", "max"),
        first_order=("order_timestamp", "min"),
        frequency=("order_id", "nunique"),
        monetary=("line_total", "sum"),
        distinct_items=("menu_item_id", "nunique"),
    ).reset_index()

    # recency من نهايه النافذه
    cutoff = pd.Timestamp(FEATURE_WINDOW_END)
    feats["recency"] = (cutoff - feats["last_order"]).dt.days

    # متوسط قيمه الطلب
    feats["aov"] = (feats["monetary"] / feats["frequency"]).round(2)

    return feats


def build_item_features(orders, items):
    # ننضم التفاصيل مع الطلبات
    joined = items.merge(
        orders[["order_id", "order_timestamp"]],
        on="order_id",
        how="inner",
    )

    # نحسب التكلفه على مستوى السطر
    joined["line_cost"] = joined["quantity"] * joined["unit_cost"]

    # الميزات الاساسيه لكل صنف
    feats = joined.groupby("menu_item_id").agg(
        qty_sold=("quantity", "sum"),
        revenue=("line_total", "sum"),
        cost=("line_cost", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index()

    # هامش المساهمه ونسبته
    feats["margin"] = (feats["revenue"] - feats["cost"]).round(2)
    feats["margin_pct"] = (
        feats["margin"] / feats["revenue"].replace(0, pd.NA)
    ).round(4)

    return feats


def run():
    log.info("نبدا بناء الميزات")
    src = load_sources()

    orders = clean_orders(src["orders"])
    orders = filter_features_window(orders)
    log.info(f"الطلبات داخل النافذه: {len(orders):,}")

    # features العملاء
    cust = build_customer_features(orders, src["items"])
    save_stage(cust, "02_feature_store", "customer_features.parquet")
    log.info(f"customer features: {len(cust):,} صف")

    # features الاصناف
    item = build_item_features(orders, src["items"])
    save_stage(item, "02_feature_store", "item_features.parquet")
    log.info(f"item features: {len(item):,} صف")


if __name__ == "__main__":
    run()
    
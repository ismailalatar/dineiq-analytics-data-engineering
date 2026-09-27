"""
نحلل التقييمات حسب SRS Step 29
نربطها مع: الصنف والموقع والربحيه والمبيعات
واعاده الشراء والفتره الزمنيه والعروض
ونكشف الشواذ حسب SRS Step 30
المخرجات تروح لمجلد 09_ratings
"""

import pandas as pd

from python_pipeline.config import RATING_HIGH, RATING_LOW, Z_THRESHOLD
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_ratings():
    r = load_clean_table("Ratings")
    r["rating_timestamp"] = pd.to_datetime(r["rating_timestamp"])
    r["date"] = r["rating_timestamp"].dt.normalize()
    return r


def by_item(r, menu, items):
    # متوسط التقييم لكل صنف مع الربحيه والمبيعات واعاده الشراء
    agg = r.groupby("menu_item_id").agg(
        avg_rating=("rating_value", "mean"),
        n_ratings=("rating_id", "count"),
        std_rating=("rating_value", "std"),
    ).reset_index()
    agg["avg_rating"] = agg["avg_rating"].round(2)
    agg["std_rating"] = agg["std_rating"].round(2)

    # نضيف المبيعات والربحيه
    items["line_cost"] = items["quantity"] * items["unit_cost"]
    items["line_margin"] = items["line_total"] - items["line_cost"]

    sales = items.groupby("menu_item_id").agg(
        qty_sold=("quantity", "sum"),
        revenue=("line_total", "sum"),
        margin=("line_margin", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index()
    # اعاده الشراء = عدد الطلبات - 1
    sales["repeat_purchase"] = (sales["orders"] - 1).clip(lower=0)

    agg = agg.merge(sales, on="menu_item_id", how="left")
    agg = agg.merge(menu[["menu_item_id", "item_name", "category_id"]],
                    on="menu_item_id", how="left")

    # فجوه بين التقييم والمبيعات
    median_qty = agg["qty_sold"].median()
    agg["rating_sales_mismatch"] = (
        (agg["avg_rating"] >= 4.3) & (agg["qty_sold"] < median_qty)
    ) | (
        (agg["avg_rating"] <= 2.5) & (agg["qty_sold"] > median_qty)
    )

    return agg.sort_values("avg_rating", ascending=False)


def by_location(r, orders):
    # متوسط التقييم لكل موقع
    agg = r.groupby("restaurant_id").agg(
        avg_rating=("rating_value", "mean"),
        n_ratings=("rating_id", "count"),
        std_rating=("rating_value", "std"),
    ).reset_index()
    agg["avg_rating"] = agg["avg_rating"].round(2)
    agg["std_rating"] = agg["std_rating"].round(2)

    # نضيف مبيعات الموقع
    sales = orders.groupby("restaurant_id").agg(
        n_orders=("order_id", "count"),
        total_revenue=("total_amount", "sum"),
    ).reset_index()
    agg = agg.merge(sales, on="restaurant_id", how="left")

    return agg.sort_values("avg_rating", ascending=False)


def by_time(r):
    # تحليل زمني
    r2 = r.copy()
    r2["month"] = r2["rating_timestamp"].dt.month
    r2["dow"] = r2["rating_timestamp"].dt.day_name()
    return r2.groupby(["month", "dow"]).agg(
        avg_rating=("rating_value", "mean"),
        n_ratings=("rating_id", "count"),
    ).reset_index().round({"avg_rating": 2})


def by_promotion(r, orders):
    # مقارنه التقييمات بين فترات العروض وغير العروض
    o = orders.copy()
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    promo_dates = set(
        o[o["promotion_id"].notna()]["order_timestamp"].dt.normalize().unique()
    )

    r2 = r.copy()
    r2["has_promo"] = r2["date"].isin(promo_dates)

    return r2.groupby("has_promo").agg(
        avg_rating=("rating_value", "mean"),
        n_ratings=("rating_id", "count"),
    ).reset_index().round({"avg_rating": 2})


def anomalies(r):
    # نحسب عدد التقييمات اليوميه لكل صنف ونكشف الشواذ
    daily = r.groupby(["menu_item_id", "date"]).agg(
        n=("rating_id", "count"),
        avg=("rating_value", "mean"),
        daily_std=("rating_value", "std"),
    ).reset_index()

    stats = daily.groupby("menu_item_id")["n"].agg(
        n_mean="mean", n_std="std"
    ).reset_index()
    daily = daily.merge(stats, on="menu_item_id", how="left")
    daily["z"] = (daily["n"] - daily["n_mean"]) / daily["n_std"].replace(0, float("nan"))

    daily["type"] = None

    # تركيز: عدد كبير غير طبيعي
    daily.loc[daily["z"] > Z_THRESHOLD, "type"] = "concentration"

    # ارتفاع: عدد كافي + متوسط مرتفع
    spike_mask = (daily["n"] >= 5) & (daily["avg"] >= RATING_HIGH)
    daily.loc[spike_mask & daily["type"].isna(), "type"] = "spike"

    # انخفاض: عدد كافي + متوسط منخفض
    drop_mask = (daily["n"] >= 5) & (daily["avg"] <= RATING_LOW)
    daily.loc[drop_mask & daily["type"].isna(), "type"] = "drop"

    # تقييمات متطابقه (std = 0) مع عدد كبير
    identical_mask = (daily["n"] >= 10) & (daily["daily_std"] == 0)
    daily.loc[identical_mask & daily["type"].isna(), "type"] = "identical"

    return daily[daily["type"].notna()].copy()


def inconsistencies(by_item_df):
    # حالات عدم اتساق بين التقييم والشراء
    return by_item_df[by_item_df["rating_sales_mismatch"] == True].copy()


def run():
    log.info("نبدا rating analysis")
    r = load_ratings()
    menu = load_clean_table("Menu_Items")
    items = load_clean_table("Order_Items")
    orders = load_clean_table("Orders")

    # SRS Step 29 - التحليل الشامل
    save_stage(by_item(r, menu, items), "09_ratings", "ratings_by_item.parquet")
    save_stage(by_location(r, orders), "09_ratings", "ratings_by_location.parquet")
    save_stage(by_time(r), "09_ratings", "ratings_by_time.parquet")
    save_stage(by_promotion(r, orders), "09_ratings", "ratings_by_promotion.parquet")

    # SRS Step 30 - الشواذ
    an = anomalies(r)
    save_stage(an, "09_ratings", "rating_anomalies.parquet")

    # حالات عدم الاتساق
    incon = inconsistencies(by_item(r, menu, items))
    save_stage(incon, "09_ratings", "rating_inconsistencies.parquet")

    log.info(f"خلصنا - {len(r):,} تقييم")
    log.info(f"انواع الشواذ:\n{an['type'].value_counts().to_string()}")
    log.info(f"حالات عدم الاتساق: {len(incon)}")


if __name__ == "__main__":
    run()
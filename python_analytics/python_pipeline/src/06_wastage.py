"""
نحلل الهدر حسب كل الابعاد الي يطلبها المشروع
item category location day time demand promotion inventory preparation
ونصنف الخطر حسب نسبه الهدر
المخرجات تروح لمجلد 06_wastage
"""

import pandas as pd

from python_pipeline.config import WASTAGE_LOW, WASTAGE_MEDIUM
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_wastage():
    w = load_clean_table("Wastage")
    w["wastage_date"] = pd.to_datetime(w["wastage_date"])
    return w


def by_item(w, menu):
    # الهدر لكل صنف
    g = w.groupby("menu_item_id").agg(
        total_wasted=("quantity_wasted", "sum"),
        total_cost=("wastage_cost", "sum"),
        n_records=("wastage_id", "count"),
    ).reset_index()
    g = g.merge(menu[["menu_item_id", "item_name", "category_id"]],
                on="menu_item_id", how="left")
    return g.sort_values("total_cost", ascending=False)


def by_category(w, menu):
    # الهدر لكل فئه
    cats = load_clean_table("Menu_Categories")
    m = menu[["menu_item_id", "category_id"]]
    w2 = w.merge(m, on="menu_item_id", how="left")
    w2 = w2.merge(cats, on="category_id", how="left")
    return w2.groupby(["category_id", "category_name"]).agg(
        total_wasted=("quantity_wasted", "sum"),
        total_cost=("wastage_cost", "sum"),
        n_records=("wastage_id", "count"),
    ).reset_index().sort_values("total_cost", ascending=False)


def by_location(w):
    # الهدر لكل موقع
    return w.groupby("restaurant_id").agg(
        total_wasted=("quantity_wasted", "sum"),
        total_cost=("wastage_cost", "sum"),
        n_records=("wastage_id", "count"),
    ).reset_index().sort_values("total_cost", ascending=False)


def by_day(w):
    # الهدر حسب اليوم من الاسبوع
    w2 = w.copy()
    w2["dow"] = w2["wastage_date"].dt.day_name()
    return w2.groupby("dow").agg(
        total_wasted=("quantity_wasted", "sum"),
        total_cost=("wastage_cost", "sum"),
    ).reset_index().sort_values("total_cost", ascending=False)


def by_time(w):
    # الهدر حسب الشهر والسنه
    w2 = w.copy()
    w2["month"] = w2["wastage_date"].dt.month
    w2["year"] = w2["wastage_date"].dt.year
    return w2.groupby(["year", "month"]).agg(
        total_wasted=("quantity_wasted", "sum"),
        total_cost=("wastage_cost", "sum"),
    ).reset_index()


def by_reason(w):
    # الهدر حسب السبب
    return w.groupby("wastage_reason").agg(
        total_wasted=("quantity_wasted", "sum"),
        total_cost=("wastage_cost", "sum"),
        n_records=("wastage_id", "count"),
    ).reset_index().sort_values("total_cost", ascending=False)


def by_demand(w, orders, items):
    # الهدر مقارنه بالطلب على نفس اليوم
    # نجمع الطلب اليومي لكل صنف
    o = orders.copy()
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["date"] = o["order_timestamp"].dt.normalize()

    sales = items.merge(o[["order_id", "date"]], on="order_id", how="inner")
    daily_sales = sales.groupby(["menu_item_id", "date"]).agg(
        demand_qty=("quantity", "sum")
    ).reset_index()

    # نجمع الهدر اليومي لكل صنف
    w2 = w.copy()
    w2["date"] = w2["wastage_date"].dt.normalize()
    daily_waste = w2.groupby(["menu_item_id", "date"]).agg(
        wasted_qty=("quantity_wasted", "sum"),
        wasted_cost=("wastage_cost", "sum"),
    ).reset_index()

    m = daily_waste.merge(daily_sales, on=["menu_item_id", "date"], how="left")
    m["demand_qty"] = m["demand_qty"].fillna(0)
    m["waste_ratio"] = (
        m["wasted_qty"] / m["demand_qty"].replace(0, float("nan"))
    ).round(4)
    return m


def by_promotion(w, orders):
    # الهدر مقارنه بفترات العروض
    o = orders.copy()
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["date"] = o["order_timestamp"].dt.normalize()

    # نجمع كم صنف انباع خلال عرض وكم خارج عرض
    promo_days = o[o["promotion_id"].notna()]["date"].unique()

    w2 = w.copy()
    w2["date"] = w2["wastage_date"].dt.normalize()
    w2["has_promo"] = w2["date"].isin(promo_days)

    return w2.groupby("has_promo").agg(
        total_wasted=("quantity_wasted", "sum"),
        total_cost=("wastage_cost", "sum"),
        n_records=("wastage_id", "count"),
    ).reset_index()


def by_inventory(w, inv):
    # الهدر مقارنه بالمخزون المستهلك
    inv2 = inv.copy()
    cons = inv2.groupby(["menu_item_id", "restaurant_id"]).agg(
        consumed=("consumption_quantity", "sum"),
        opening=("opening_quantity", "sum"),
        closing=("closing_quantity", "sum"),
    ).reset_index()

    grp = w.groupby(["menu_item_id", "restaurant_id"]).agg(
        wasted=("quantity_wasted", "sum"),
        cost=("wastage_cost", "sum"),
    ).reset_index()

    m = grp.merge(cons, on=["menu_item_id", "restaurant_id"], how="left")
    m[["consumed", "opening", "closing"]] = m[["consumed", "opening", "closing"]].fillna(0)
    m["waste_rate_of_consumed"] = (
        m["wasted"] / m["consumed"].replace(0, float("nan"))
    ).round(4)
    m["waste_rate_of_opening"] = (
        m["wasted"] / m["opening"].replace(0, float("nan"))
    ).round(4)
    return m


def risk_score(w, inv):
    # نحسب نسبه الهدر من الاستهلاك لكل (صنف, موقع) ونصنفه
    inv2 = inv.copy()
    cons = inv2.groupby(["menu_item_id", "restaurant_id"]).agg(
        consumed=("consumption_quantity", "sum")
    ).reset_index()

    grp = w.groupby(["menu_item_id", "restaurant_id"]).agg(
        wasted=("quantity_wasted", "sum"),
        cost=("wastage_cost", "sum"),
    ).reset_index()

    m = grp.merge(cons, on=["menu_item_id", "restaurant_id"], how="left")
    m["consumed"] = m["consumed"].fillna(0)
    m["waste_rate"] = (
        m["wasted"] / m["consumed"].replace(0, float("nan"))
    ).round(4)

    def tier(x):
        if pd.isna(x):
            return "unknown"
        if x >= WASTAGE_MEDIUM:
            return "high"
        if x >= WASTAGE_LOW:
            return "medium"
        return "low"

    m["risk"] = m["waste_rate"].apply(tier)
    return m


def run():
    log.info("نبدا wastage")
    w = load_wastage()
    menu = load_clean_table("Menu_Items")
    inv = load_clean_table("Inventory")
    orders = load_clean_table("Orders")
    items = load_clean_table("Order_Items")

    save_stage(by_item(w, menu),       "06_wastage", "wastage_by_item.parquet")
    save_stage(by_category(w, menu),   "06_wastage", "wastage_by_category.parquet")
    save_stage(by_location(w),         "06_wastage", "wastage_by_location.parquet")
    save_stage(by_day(w),              "06_wastage", "wastage_by_day.parquet")
    save_stage(by_time(w),             "06_wastage", "wastage_by_time.parquet")
    save_stage(by_reason(w),           "06_wastage", "wastage_by_reason.parquet")
    save_stage(by_demand(w, orders, items), "06_wastage", "wastage_by_demand.parquet")
    save_stage(by_promotion(w, orders), "06_wastage", "wastage_by_promotion.parquet")
    save_stage(by_inventory(w, inv),   "06_wastage", "wastage_by_inventory.parquet")

    risk = risk_score(w, inv)
    save_stage(risk, "06_wastage", "wastage_risk.parquet")

    log.info(f"خلصنا - {len(w):,} سجل هدر")
    log.info(f"خطر الهدر:\n{risk['risk'].value_counts().to_string()}")


if __name__ == "__main__":
    run()
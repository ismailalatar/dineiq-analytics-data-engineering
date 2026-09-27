"""
Slow-Moving Dishes Detection (SRS Step 32)
==========================================

Criteria used (SRS Step 32):
- Low sales volume
- Low purchase frequency
- Long gaps between purchases
- Low repeat purchase
- High wastage
- Weak profitability
- Poor trend

An item is classified as slow-moving if it meets at least 2 of these criteria.
"""

import pandas as pd

from python_pipeline.config import FEATURE_WINDOW_END
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_sales():
    # نقرا المبيعات لكل صنف
    i = load_clean_table("Order_Items")
    o = load_clean_table("Orders")
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])

    m = i.merge(
        o[["order_id", "order_timestamp", "customer_id"]],
        on="order_id",
        how="inner",
    )

    m["quantity"] = pd.to_numeric(m["quantity"], errors="coerce").fillna(0)
    m["line_total"] = pd.to_numeric(m["line_total"], errors="coerce").fillna(0)
    m["unit_cost"] = pd.to_numeric(m["unit_cost"], errors="coerce").fillna(0)

    m["line_cost"] = m["quantity"] * m["unit_cost"]
    m["line_margin"] = m["line_total"] - m["line_cost"]

    agg = m.groupby("menu_item_id").agg(
        qty_sold=("quantity", "sum"),
        revenue=("line_total", "sum"),
        margin=("line_margin", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        last_sale=("order_timestamp", "max"),
        first_sale=("order_timestamp", "min"),
    ).reset_index()

    # H1/H2 للاتجاه
    m["half"] = (m["order_timestamp"].dt.month <= 6).map({True: "h1", False: "h2"})
    halves = m.groupby(["menu_item_id", "half"])["quantity"].sum().unstack(fill_value=0)
    halves.columns = ["h1_qty", "h2_qty"]
    agg = agg.merge(halves, on="menu_item_id", how="left")

    # فجوات زمنيه
    def avg_gap(s):
        s = s.sort_values()
        if len(s) < 2:
            return 0
        return s.diff().dt.days.mean()

    gaps = m.groupby("menu_item_id")["order_timestamp"].apply(avg_gap).reset_index()
    gaps.columns = ["menu_item_id", "avg_days_between_orders"]
    agg = agg.merge(gaps, on="menu_item_id", how="left")

    # اعاده الشراء
    agg["repeat_purchase"] = (agg["orders"] - 1).clip(lower=0)

    return agg


def load_wastage():
    # الهدر لكل صنف
    w = load_clean_table("Wastage")
    w["quantity_wasted"] = pd.to_numeric(w["quantity_wasted"], errors="coerce").fillna(0)
    return w.groupby("menu_item_id").agg(
        total_wasted=("quantity_wasted", "sum"),
        wastage_cost=("wastage_cost", "sum"),
    ).reset_index()


def classify_slow_moving(agg, menu, wastage):
    # نصنف حسب المعايير السبعه
    agg = agg.merge(wastage, on="menu_item_id", how="left")
    agg[["total_wasted", "wastage_cost"]] = agg[["total_wasted", "wastage_cost"]].fillna(0)

    # Q للthresholds
    q25_qty = agg["qty_sold"].quantile(0.25)
    q25_rev = agg["revenue"].quantile(0.25)
    q25_freq = agg["orders"].quantile(0.25)
    q75_gap = agg["avg_days_between_orders"].quantile(0.75)
    q25_repeat = agg["repeat_purchase"].quantile(0.25)
    q75_waste = agg["total_wasted"].quantile(0.75)
    q25_margin = agg["margin"].quantile(0.25)

    agg = agg.copy()

    # 1. low sales volume
    agg["c_low_volume"] = agg["qty_sold"] <= q25_qty

    # 2. low purchase frequency
    agg["c_low_frequency"] = agg["orders"] <= q25_freq

    # 3. long gaps between purchases
    agg["c_long_gaps"] = agg["avg_days_between_orders"] >= q75_gap

    # 4. low repeat purchase
    agg["c_low_repeat"] = agg["repeat_purchase"] <= q25_repeat

    # 5. high wastage
    agg["c_high_wastage"] = agg["total_wasted"] >= q75_waste

    # 6. weak profitability
    agg["c_weak_margin"] = agg["margin"] <= q25_margin

    # 7. poor trend: H2 < H1
    agg["c_poor_trend"] = agg["h2_qty"] < agg["h1_qty"]

    # العدد الكلي
    criteria = ["c_low_volume", "c_low_frequency", "c_long_gaps",
                "c_low_repeat", "c_high_wastage", "c_weak_margin", "c_poor_trend"]
    agg["criteria_met"] = agg[criteria].sum(axis=1)
    agg["is_slow_moving"] = agg["criteria_met"] >= 2

    # نضيف الاسم
    agg = agg.merge(
        menu[["menu_item_id", "item_name", "category_id", "base_price"]],
        on="menu_item_id",
        how="left",
    )

    return agg


def no_recent_sales(agg):
    # الاصناف الي ما انباعت في اخر 90 يوم
    cutoff = pd.Timestamp(FEATURE_WINDOW_END) - pd.Timedelta(days=90)
    agg = agg.copy()
    agg["no_recent_sale"] = agg["last_sale"] < cutoff
    return agg


def run():
    log.info("Starting slow-moving dishes detection")
    agg = load_sales()
    menu = load_clean_table("Menu_Items")
    wastage = load_wastage()

    agg = classify_slow_moving(agg, menu, wastage)
    agg = no_recent_sales(agg)

    slow = agg[agg["is_slow_moving"]].copy()
    slow = slow.sort_values(["criteria_met", "qty_sold"], ascending=[False, True]).reset_index(drop=True)

    save_stage(agg, "12_slow_moving", "item_sales_summary.parquet")
    save_stage(slow, "12_slow_moving", "slow_moving_dishes.parquet")

    no_rec = agg[agg["no_recent_sale"]].copy()
    save_stage(no_rec, "12_slow_moving", "no_recent_sales.parquet")

    log.info(f"total items: {len(agg)}")
    log.info(f"slow-moving items: {len(slow)}")
    log.info(f"criteria distribution:")
    log.info(f"\n{agg['criteria_met'].value_counts().sort_index().to_string()}")


if __name__ == "__main__":
    run()
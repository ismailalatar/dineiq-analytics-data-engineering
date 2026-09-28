"""
Estimated Price Elasticity (Observational)
==========================================

This is an OBSERVATIONAL analysis, not a causal experiment.

Two approaches:
1. Univariate elasticity: cov(qty_pct, price_pct) / var(price_pct)
2. Multivariate elasticity: log(qty) = b0 + b1*log(price) + controls
   - Controls: has_promo, weekend, month
   - Multivariate elasticity = coefficient of log(price)

The classification reflects observed association, not causal effect.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_daily_sales():
    items = load_clean_table("Order_Items")
    orders = load_clean_table("Orders")
    orders["order_timestamp"] = pd.to_datetime(orders["order_timestamp"])
    orders["date"] = orders["order_timestamp"].dt.normalize()

    m = items.merge(orders[["order_id", "date"]], on="order_id", how="inner")

    m["line_cost"] = m["quantity"] * m["unit_cost"]
    m["line_margin"] = m["line_total"] - m["line_cost"]

    daily = m.groupby(["menu_item_id", "date"]).agg(
        qty=("quantity", "sum"),
        avg_price=("unit_price", "mean"),
        revenue=("line_total", "sum"),
        margin=("line_margin", "sum"),
        discount=("discount_amount", "sum"),
    ).reset_index()

    # نحوّل للانواع رقميه
    for c in ["qty", "avg_price", "revenue", "margin", "discount"]:
        daily[c] = pd.to_numeric(daily[c], errors="coerce").astype(float)

    return daily


def add_rating_and_repeat(daily):
    r = load_clean_table("Ratings")
    r["rating_value"] = pd.to_numeric(r["rating_value"], errors="coerce")
    rating = r.groupby("menu_item_id")["rating_value"].mean().rename("avg_rating")

    items = load_clean_table("Order_Items")
    repeat = items.groupby("menu_item_id").agg(
        orders=("order_id", "nunique"),
        qty_total=("quantity", "sum"),
    )
    repeat["repeat_purchase"] = (repeat["orders"] - 1).clip(lower=0)
    repeat = repeat[["repeat_purchase"]]

    return rating, repeat


def compute_elasticity(daily):
    rows = []
    for item, g in daily.groupby("menu_item_id"):
        if len(g) < 20:
            continue

        g = g.sort_values("date")
        g["price_pct"] = g["avg_price"].pct_change()
        g["qty_pct"] = g["qty"].pct_change()

        g = g.replace([np.inf, -np.inf], np.nan).dropna(
            subset=["price_pct", "qty_pct"]
        )
        g = g[(g["price_pct"].abs() < 0.5) & (g["qty_pct"].abs() < 2.0)]

        if len(g) < 10 or g["price_pct"].std() == 0:
            continue

        beta = g["qty_pct"].cov(g["price_pct"]) / g["price_pct"].var()
        corr = g["qty_pct"].corr(g["price_pct"])

        if pd.isna(beta) or abs(beta) > 10:
            continue

        rev_corr = g["avg_price"].corr(g["revenue"]) if "revenue" in g.columns else None
        marg_corr = g["avg_price"].corr(g["margin"]) if "margin" in g.columns else None
        disc_corr = g["avg_price"].corr(g["discount"]) if "discount" in g.columns else None

        rows.append({
            "menu_item_id": item,
            "elasticity": round(beta, 4),
            "correlation": round(corr, 4),
            "price_revenue_corr": round(rev_corr, 4) if rev_corr is not None else None,
            "price_margin_corr": round(marg_corr, 4) if marg_corr is not None else None,
            "price_discount_corr": round(disc_corr, 4) if disc_corr is not None else None,
            "n_days": len(g),
            "avg_price": round(g["avg_price"].mean(), 2),
            "avg_qty": round(g["qty"].mean(), 2),
        })

    return pd.DataFrame(rows)


def classify(df):
    def tier(e):
        if pd.isna(e):
            return "unknown"
        a = abs(e)
        if a >= 1.5:
            return "high"
        if a >= 0.5:
            return "medium"
        return "low"

    df = df.copy()
    df["sensitivity"] = df["elasticity"].apply(tier)
    return df


def add_names(df):
    menu = load_clean_table("Menu_Items")
    return df.merge(
        menu[["menu_item_id", "item_name", "category_id"]],
        on="menu_item_id",
        how="left",
    )


def add_rating_repeat(df, rating, repeat):
    df = df.merge(rating, left_on="menu_item_id", right_index=True, how="left")
    df = df.merge(repeat, left_on="menu_item_id", right_index=True, how="left")
    return df


def multivariate_elasticity(daily, orders):
    """نموذج انحدار متعدد لحساب elasticity مع السيطره على عوامل اخرى"""
    d = daily.copy()

    # نضمن ان القيم موجبه
    d = d[d["qty"] > 0].copy()
    d = d[d["avg_price"] > 0].copy()

    # نحوّل للانواع رقميه بطريقه آمنه
    d["avg_price"] = pd.to_numeric(d["avg_price"], errors="coerce").astype(float)
    d["qty"] = pd.to_numeric(d["qty"], errors="coerce").astype(float)

    d = d.dropna(subset=["avg_price", "qty"])
    d = d[d["avg_price"] > 0]
    d = d[d["qty"] > 0]

    if len(d) == 0:
        return pd.DataFrame()

    # log
    d["log_price"] = np.log(d["avg_price"].astype(float))
    d["log_qty"] = np.log(d["qty"].astype(float))

    # عوامل اضافيه من الطلبات
    o = orders.copy()
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["date"] = o["order_timestamp"].dt.normalize()
    o["weekend"] = (o["order_timestamp"].dt.dayofweek >= 5).astype(int)
    o["month"] = o["order_timestamp"].dt.month
    o["has_promo"] = o["promotion_id"].notna().astype(int)

    daily_extras = o.groupby("date").agg(
        has_promo=("has_promo", "max"),
        weekend=("weekend", "max"),
        month=("month", "first"),
    ).reset_index()

    d = d.merge(daily_extras, on="date", how="left")
    d[["has_promo", "weekend"]] = d[["has_promo", "weekend"]].fillna(0)
    d["month"] = d["month"].fillna(0)

    rows = []
    for item, g in d.groupby("menu_item_id"):
        if len(g) < 30:
            continue

        X = g[["log_price", "has_promo", "weekend", "month"]].values.astype(float)
        y = g["log_qty"].values.astype(float)

        # نتحقق من صحة البيانات
        if np.isnan(X).any() or np.isnan(y).any():
            continue

        try:
            model = LinearRegression()
            model.fit(X, y)
            elasticity = float(model.coef_[0])
            r2 = float(model.score(X, y))

            rows.append({
                "menu_item_id": item,
                "multivariate_elasticity": round(elasticity, 4),
                "model_r2": round(r2, 4),
                "n_days": int(len(g)),
                "has_promo_coef": round(float(model.coef_[1]), 4),
                "weekend_coef": round(float(model.coef_[2]), 4),
            })
        except Exception as e:
            log.warning(f"skip item {item}: {e}")
            continue

    return pd.DataFrame(rows)


def classify_multivariate(df):
    def tier(e):
        if pd.isna(e):
            return "insufficient_evidence"
        if e >= -0.5:
            return "inelastic"
        if e >= -1.5:
            return "moderately_elastic"
        return "elastic"

    df = df.copy()
    df["mv_class"] = df["multivariate_elasticity"].apply(tier)
    return df


def run():
    log.info("نبدا price analysis")
    daily = load_daily_sales()
    log.info(f"daily sales: {len(daily):,} صف")

    el = compute_elasticity(daily)
    log.info(f"items with elasticity: {len(el):,}")

    el = classify(el)
    el = add_names(el)

    rating, repeat = add_rating_and_repeat(daily)
    el = add_rating_repeat(el, rating, repeat)

    el = el.sort_values("elasticity").reset_index(drop=True)

    save_stage(el, "07_price", "price_elasticity.parquet")
    log.info(f"خلصنا - {len(el):,} صنف")
    log.info(f"توزيع الحساسيه:\n{el['sensitivity'].value_counts().to_string()}")

    # price vs repeat purchase
    items = load_clean_table("Order_Items")
    order_counts = items.groupby("menu_item_id")["order_id"].nunique().reset_index()
    order_counts["repeat_purchase"] = (order_counts["order_id"] - 1).clip(lower=0)

    menu = load_clean_table("Menu_Items")
    avg_price = items.groupby("menu_item_id")["unit_price"].mean().reset_index()
    avg_price.columns = ["menu_item_id", "avg_unit_price"]

    price_repeat = avg_price.merge(
        order_counts[["menu_item_id", "repeat_purchase"]],
        on="menu_item_id", how="left"
    )
    price_repeat = price_repeat.merge(
        menu[["menu_item_id", "item_name", "category_id"]],
        on="menu_item_id", how="left"
    )

    corr = price_repeat["avg_unit_price"].corr(price_repeat["repeat_purchase"])
    price_repeat["price_repeat_corr"] = round(corr, 4)
    save_stage(price_repeat, "07_price", "price_vs_repeat_purchase.parquet")
    log.info(f"price vs repeat: {len(price_repeat)} items, corr={corr:.4f}")

    # multivariate elasticity
    orders = load_clean_table("Orders")
    mv = multivariate_elasticity(daily, orders)
    if len(mv):
        mv = classify_multivariate(mv)
        menu2 = load_clean_table("Menu_Items")
        mv = mv.merge(menu2[["menu_item_id", "item_name"]], on="menu_item_id", how="left")
        save_stage(mv, "07_price", "multivariate_elasticity.parquet")
        log.info(f"multivariate elasticity: {len(mv)} items")
        log.info(f"distribution:\n{mv['mv_class'].value_counts().to_string()}")

    # summary
    summary = pd.DataFrame([{
        "n_items": len(el),
        "high_sensitivity": int((el["sensitivity"] == "high").sum()),
        "medium_sensitivity": int((el["sensitivity"] == "medium").sum()),
        "low_sensitivity": int((el["sensitivity"] == "low").sum()),
        "avg_price_revenue_corr": round(el["price_revenue_corr"].mean(), 4),
        "avg_price_margin_corr": round(el["price_margin_corr"].mean(), 4),
        "avg_price_discount_corr": round(el["price_discount_corr"].mean(), 4),
        "price_repeat_corr": round(corr, 4),
    }])
    save_stage(summary, "07_price", "price_summary.parquet")


if __name__ == "__main__":
    run()
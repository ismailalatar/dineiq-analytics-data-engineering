"""
نحلل فعاليه العروض بشكل شامل حسب SRS Steps 27 و 28
نقارن قبل خلال بعد لكل حمله على اصناف الحملة فقط
نضيف تحليل العملاء الجدد والعائدين و aov والهدر
ونكشف 5 انواع من الفخاخ
الحمله تعتبر فخ اذا حققت معيارين على الاقل
المخرجات تروح لمجلد 08_promotion
"""

import pandas as pd

from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)

PRE_WINDOW_DAYS = 14
POST_WINDOW_DAYS = 14


def load_merged():
    # ندمج الطلبات مع التفاصيل عشان نحسب ربح لكل سطر
    o = load_clean_table("Orders")
    i = load_clean_table("Order_Items")
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])

    m = i.merge(
        o[["order_id", "customer_id", "order_timestamp", "promotion_id"]],
        on="order_id",
        how="inner",
    )
    m["line_cost"] = m["quantity"] * m["unit_cost"]
    m["line_profit"] = m["line_total"] - m["line_cost"]
    return m


def load_wastage():
    w = load_clean_table("Wastage")
    w["wastage_date"] = pd.to_datetime(w["wastage_date"])
    return w


def window_metrics(df):
    if len(df) == 0:
        return {
            "revenue": 0, "profit": 0, "orders": 0,
            "customers": 0, "aov": 0, "qty": 0,
            "avg_margin_pct": 0,
        }
    orders = df["order_id"].nunique()
    customers = df["customer_id"].nunique()
    revenue = df["line_total"].sum()
    profit = df["line_profit"].sum()
    margin_pct = profit / revenue if revenue else 0

    return {
        "revenue": round(revenue, 2),
        "profit": round(profit, 2),
        "orders": int(orders),
        "customers": int(customers),
        "aov": round(revenue / orders, 2) if orders else 0,
        "qty": int(df["quantity"].sum()),
        "avg_margin_pct": round(margin_pct, 4),
    }


def customer_behavior(during, pre):
    during_customers = set(during["customer_id"].unique())
    pre_customers = set(pre["customer_id"].unique())
    new_customers = during_customers - pre_customers
    repeat_customers = during_customers & pre_customers

    return {
        "new_customers": len(new_customers),
        "repeat_customers": len(repeat_customers),
        "total_customers_during": len(during_customers),
        "total_customers_pre": len(pre_customers),
        "acquisition_rate": round(
            len(new_customers) / len(during_customers), 4
        ) if during_customers else 0,
        "repeat_rate": round(
            len(repeat_customers) / len(during_customers), 4
        ) if during_customers else 0,
    }


def wastage_metrics(w, start, end, items_in_promo):
    during = w[
        (w["wastage_date"] >= start)
        & (w["wastage_date"] <= end)
        & (w["menu_item_id"].isin(items_in_promo))
    ]
    pre = w[
        (w["wastage_date"] >= start - pd.Timedelta(days=PRE_WINDOW_DAYS))
        & (w["wastage_date"] < start)
        & (w["menu_item_id"].isin(items_in_promo))
    ]

    during_qty = float(during["quantity_wasted"].sum())
    pre_qty = float(pre["quantity_wasted"].sum())
    pct_change = (
        (during_qty - pre_qty) / pre_qty * 100
    ) if pre_qty > 0 else 0

    return {
        "wastage_qty": round(during_qty, 2),
        "wastage_cost": round(float(during["wastage_cost"].sum()), 2),
        "wastage_records": int(len(during)),
        "pre_wastage_qty": round(pre_qty, 2),
        "wastage_pct_change": round(pct_change, 2),
    }


def promo_only_purchases(m, start, end, items_in_promo):
    # نحسب كم عميل اشترى فقط خلال العرض
    window_start = start - pd.Timedelta(days=PRE_WINDOW_DAYS)
    sub = m[
        (m["menu_item_id"].isin(items_in_promo))
        & (m["order_timestamp"] >= window_start)
        & (m["order_timestamp"] <= end)
    ]
    during_customers = set(
        sub[(sub["order_timestamp"] >= start) & (sub["order_timestamp"] <= end)]["customer_id"]
    )
    pre_customers = set(
        sub[(sub["order_timestamp"] < start)]["customer_id"]
    )
    promo_only = during_customers - pre_customers
    return {
        "promo_only_customers": len(promo_only),
        "promo_only_rate": round(
            len(promo_only) / len(during_customers), 4
        ) if during_customers else 0,
    }


def detect_traps(eff):
    # نكشف الفخاخ حسب SRS Step 28
    eff = eff.copy()

    # 1. sales increase but profit decreases
    eff["trap_sales_profit"] = (
        (eff["delta_revenue"] > 0) & (eff["delta_profit"] < 0)
    )

    # 2. customers increase but avg margin drops بشكل واضح
    eff["trap_customers_margin"] = (
        (eff["during_customers"] > eff["pre_customers"])
        & (eff["delta_margin_pct"] < -0.10)
    )

    # 3. promotion increases wastage بنسبه كبيره
    # نطلب زياده 50 بالميه على الاقل
    eff["trap_wastage"] = (
        (eff["wastage_pct_change"] > 50) & (eff["delta_revenue"] > 0)
    )

    # 4. customers buy only during discount
    # نحسبها بمعيارين معا: نسبه عاليه جدا من عملاء العرض فقط
    # AND post_retention منخفض (لم يعودوا)
    eff["trap_promo_only"] = (
        (eff["promo_only_rate"] > 0.95)
        & (eff["post_retention"] < 0.20)
    )

    # 5. promotion shifts sales from more profitable product
    # انخفاض الربح 20 بالميه على الاقل
    eff["trap_margin_shift"] = eff["profit_pct"] < -20

    # الفخ الكلي = معيارين على الاقل
    # لكن نستبعد trap_promo_only من العد (لانه ضعيف التمييز)
    trap_sum = (
        eff["trap_sales_profit"].astype(int)
        + eff["trap_customers_margin"].astype(int)
        + eff["trap_wastage"].astype(int)
        + eff["trap_margin_shift"].astype(int)
    )
    eff["trap_count"] = trap_sum
    # نعتبره فخ اذا حقق 2 معايير من الاربعه
    # او معيار قوي واحد (sales_profit) مع margin_shift
    eff["is_trap"] = (
        (trap_sum >= 2)
        | (eff["trap_sales_profit"] & eff["trap_margin_shift"])
    )

    return eff


def analyze_promotions(m, promos, promo_items, w):
    rows = []
    for _, p in promos.iterrows():
        pid = p["promotion_id"]
        start = pd.Timestamp(p["start_date"])
        end = pd.Timestamp(p["end_date"])

        items_in_promo = set(
            promo_items[promo_items["promotion_id"] == pid]["menu_item_id"]
        )
        if not items_in_promo:
            continue

        sub = m[m["menu_item_id"].isin(items_in_promo)]

        during = sub[(sub["order_timestamp"] >= start) & (sub["order_timestamp"] <= end)]
        pre = sub[(sub["order_timestamp"] >= start - pd.Timedelta(days=PRE_WINDOW_DAYS))
                  & (sub["order_timestamp"] < start)]
        post = sub[(sub["order_timestamp"] > end)
                   & (sub["order_timestamp"] <= end + pd.Timedelta(days=POST_WINDOW_DAYS))]

        d = window_metrics(during)
        b = window_metrics(pre)
        a = window_metrics(post)

        cb = customer_behavior(during, pre)
        wm = wastage_metrics(w, start, end, items_in_promo)
        po = promo_only_purchases(m, start, end, items_in_promo)

        rows.append({
            "promotion_id": pid,
            "promotion_name": p.get("promotion_name"),
            "start_date": str(start.date()),
            "end_date": str(end.date()),
            "n_items": len(items_in_promo),
            # خلال
            "during_revenue": d["revenue"],
            "during_profit": d["profit"],
            "during_orders": d["orders"],
            "during_customers": d["customers"],
            "during_aov": d["aov"],
            "during_qty": d["qty"],
            "during_margin_pct": d["avg_margin_pct"],
            # قبل
            "pre_revenue": b["revenue"],
            "pre_profit": b["profit"],
            "pre_orders": b["orders"],
            "pre_customers": b["customers"],
            "pre_aov": b["aov"],
            "pre_qty": b["qty"],
            "pre_margin_pct": b["avg_margin_pct"],
            # بعد
            "post_revenue": a["revenue"],
            "post_profit": a["profit"],
            "post_orders": a["orders"],
            "post_aov": a["aov"],
            # الفروق
            "delta_revenue": round(d["revenue"] - b["revenue"], 2),
            "delta_profit": round(d["profit"] - b["profit"], 2),
            "delta_orders": int(d["orders"] - b["orders"]),
            "delta_qty": int(d["qty"] - b["qty"]),
            "delta_aov": round(d["aov"] - b["aov"], 2),
            "delta_margin_pct": round(d["avg_margin_pct"] - b["avg_margin_pct"], 4),
            # النسب
            "revenue_pct": round(
                (d["revenue"] - b["revenue"]) / b["revenue"] * 100, 2
            ) if b["revenue"] else 0,
            "profit_pct": round(
                (d["profit"] - b["profit"]) / abs(b["profit"]) * 100, 2
            ) if b["profit"] else 0,
            # العملاء
            "new_customers": cb["new_customers"],
            "repeat_customers": cb["repeat_customers"],
            "acquisition_rate": cb["acquisition_rate"],
            "repeat_rate": cb["repeat_rate"],
            # الهدر
            "wastage_qty": wm["wastage_qty"],
            "wastage_cost": wm["wastage_cost"],
            "wastage_records": wm["wastage_records"],
            "pre_wastage_qty": wm["pre_wastage_qty"],
            "wastage_pct_change": wm["wastage_pct_change"],
            # عملاء العرض فقط
            "promo_only_customers": po["promo_only_customers"],
            "promo_only_rate": po["promo_only_rate"],
            # ما بعد العرض
            "post_retention": round(
                a["customers"] / d["customers"], 4
            ) if d["customers"] else 0,
        })
    return pd.DataFrame(rows)


def run():
    log.info("نبدا promotion analysis")
    m = load_merged()
    promos = load_clean_table("Promotions")
    promos["start_date"] = pd.to_datetime(promos["start_date"])
    promos["end_date"] = pd.to_datetime(promos["end_date"])
    promo_items = load_clean_table("Promotion_Items")
    w = load_wastage()
    log.info(f"عدد الحملات: {len(promos)}")

    eff = analyze_promotions(m, promos, promo_items, w)
    eff = detect_traps(eff)
    save_stage(eff, "08_promotion", "promo_effectiveness.parquet")
    log.info(f"خلصنا - {len(eff)} حمله")

    # ملخص الفخاخ بانواعها
    traps_summary = pd.DataFrame([{
        "total_campaigns": len(eff),
        "trap_sales_profit": int(eff["trap_sales_profit"].sum()),
        "trap_customers_margin": int(eff["trap_customers_margin"].sum()),
        "trap_wastage": int(eff["trap_wastage"].sum()),
        "trap_promo_only": int(eff["trap_promo_only"].sum()),
        "trap_margin_shift": int(eff["trap_margin_shift"].sum()),
        "total_trap_campaigns": int(eff["is_trap"].sum()),
    }])
    save_stage(traps_summary, "08_promotion", "promo_traps_summary.parquet")
    log.info(f"\nملخص الفخاخ:\n{traps_summary.to_string(index=False)}")

    # قائمه الحملات المصنفه كفخ
    traps = eff[eff["is_trap"]][[
        "promotion_id", "promotion_name",
        "delta_revenue", "delta_profit",
        "revenue_pct", "profit_pct",
        "new_customers", "repeat_customers",
        "wastage_cost", "wastage_pct_change",
        "promo_only_rate", "trap_count",
    ]]
    save_stage(traps, "08_promotion", "promo_traps.parquet")
    log.info(f"عدد الحملات المصنفه كفخ: {len(traps)}")

    # ملخص عام
    summary = pd.DataFrame([{
        "n_campaigns": len(eff),
        "n_traps": int(eff["is_trap"].sum()),
        "avg_acquisition_rate": round(eff["acquisition_rate"].mean(), 4),
        "avg_repeat_rate": round(eff["repeat_rate"].mean(), 4),
        "avg_post_retention": round(eff["post_retention"].mean(), 4),
        "total_new_customers": int(eff["new_customers"].sum()),
        "total_wastage_cost": round(eff["wastage_cost"].sum(), 2),
    }])
    save_stage(summary, "08_promotion", "promo_summary.parquet")
    log.info(f"\nملخص: {summary.to_dict(orient='records')[0]}")


if __name__ == "__main__":
    run()
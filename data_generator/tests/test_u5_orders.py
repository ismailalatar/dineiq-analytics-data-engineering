"""U5 self-tests."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig
from data_generator.generators.dimensions import generate_dimensions
from data_generator.generators.pricing import generate_pricing_history
from data_generator.generators.promotions import generate_promotions
from data_generator.generators.orders import generate_orders_and_items


def run_u5_tests() -> bool:
    cfg = GeneratorConfig(
        seed=42,
        n_customers=5_000,
        n_restaurants=20,
        n_categories=10,
        n_menu_items=150,
        n_promotions=30,
        n_orders=10_000,
    )
    rng = np.random.default_rng(cfg.seed)
    state = generate_dimensions(cfg, rng)
    pricing = generate_pricing_history(cfg, rng, state.menu_items)
    promos, promo_items = generate_promotions(cfg, rng, state.menu_items)

    orders, order_items = generate_orders_and_items(cfg, rng, state, pricing, promos, promo_items)

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("Orders count == 10,000", len(orders) == 10_000, f"{len(orders)}")
    check("Unique order_ids == 10,000", orders["order_id"].nunique() == 10_000)
    check("Order_Items > 0", len(order_items) > 0, f"{len(order_items)}")
    avg_basket = len(order_items) / len(orders)
    check("Average basket size 5..15", 5.0 <= avg_basket <= 15.0, f"{avg_basket:.2f}")
    check("Basket size varies (std > 1.0)",
          order_items.groupby("order_id").size().std() > 1.0,
          f"std={order_items.groupby('order_id').size().std():.2f}")

    merged = order_items.assign(gross=order_items["quantity"] * order_items["unit_price"])
    merged["line_total_check"] = (merged["gross"] - merged["discount_amount"]).round(2)
    consistent = (merged["line_total"] - merged["line_total_check"]).abs() < 0.01
    check("line_total = qty*price - discount", consistent.all())

    valid_cust = set(state.customers["customer_id"])
    valid_rest = set(state.restaurants["restaurant_id"])
    valid_item = set(state.menu_items["menu_item_id"])
    check("All customer_id valid", orders["customer_id"].isin(valid_cust).all())
    check("All restaurant_id valid", orders["restaurant_id"].isin(valid_rest).all())
    check("All menu_item_id valid", order_items["menu_item_id"].isin(valid_item).all())
    check("All order_id in lines exist in orders",
          order_items["order_id"].isin(orders["order_id"]).all())

    reg_map = state.customers.set_index("customer_id")["registration_date"]
    orders_reg = pd.to_datetime(orders["customer_id"].map(reg_map))
    orders_ts = pd.to_datetime(orders["order_timestamp"])
    violations = (orders_ts.dt.normalize() < orders_reg).sum()
    check("No order before registration", violations == 0, f"{violations} violations")

    promo_lookup = promos.set_index("promotion_id")[["start_date", "end_date"]].to_dict("index")
    with_promo = orders[orders["promotion_id"].notna()].copy()
    check("Some orders have promo", len(with_promo) >= 100, f"{len(with_promo)}")
    violations_promo = 0
    for _, row in with_promo.head(1000).iterrows():
        pid = int(row["promotion_id"])
        ot = pd.Timestamp(row["order_timestamp"])
        start = pd.Timestamp(promo_lookup[pid]["start_date"])
        end_excl = pd.Timestamp(promo_lookup[pid]["end_date"]) + pd.Timedelta(days=1)
        if not (start <= ot < end_excl):
            violations_promo += 1
    check("Promo orders inside window", violations_promo == 0, f"{violations_promo} violations")

    base_map = state.menu_items.set_index("menu_item_id")["base_price"]
    lines_base = order_items["menu_item_id"].map(base_map)
    diff = (order_items["unit_price"] - lines_base).abs() / lines_base
    changed = (diff > 0.01).sum()
    check("Historical pricing applied (>10% lines changed)",
          changed / len(order_items) > 0.10,
          f"{changed}/{len(order_items)} lines")

    ts = pd.to_datetime(orders["order_timestamp"])
    dow = ts.dt.dayofweek
    weekend_share = (dow >= 4).mean()
    check("Weekend share > 0.40 (Fri/Sat/Sun)", weekend_share > 0.40, f"{weekend_share:.3f}")

    month_share = ts.dt.month.value_counts(normalize=True)
    check("Seasonal variation exists (std > 0.005)",
          month_share.std() > 0.005, f"std={month_share.std():.4f}")

    hours = ts.dt.hour
    peak_share = hours.between(11, 21).mean()
    check("Peak-hour share > 0.60", peak_share > 0.60, f"{peak_share:.3f}")

    churned = set(state.customers.loc[state.customers["_segment"] == "churned", "customer_id"])
    churned_orders = orders[orders["customer_id"].isin(churned)]
    if len(churned_orders) > 0:
        max_day = pd.to_datetime(churned_orders["order_timestamp"]).dt.normalize().max()
        cut = (cfg.end - pd.Timedelta(days=cfg.churn_customer_cutoff_days)).normalize()
        check("Churned customers stop before cutoff", max_day < cut,
              f"max={max_day.date()} cut={cut.date()}")

    oi_full = order_items.merge(orders[["order_id", "order_timestamp"]], on="order_id", how="left")
    oi_full["date"] = pd.to_datetime(oi_full["order_timestamp"]).dt.normalize()
    daily = oi_full.groupby(["menu_item_id", "date"])["quantity"].sum().reset_index()

    spikes = 0
    drops = 0
    for _, g in daily.groupby("menu_item_id"):
        if len(g) < 30:
            continue
        m = g["quantity"].mean()
        if m < 3:
            continue
        if g["quantity"].max() > m * 4:
            spikes += 1
        if g["quantity"].min() < m * 0.15:
            drops += 1

    check("Sales spike detected (max > 4x mean)", spikes >= 1, f"{spikes}")
    check("Sales drop detected (min < 15% of mean)", drops >= 1, f"{drops}")

    price_sensitive_ids = state.menu_items.loc[state.menu_items["_is_price_sensitive"], "menu_item_id"].tolist()
    daily_price = oi_full.groupby(["menu_item_id", "date"]).agg(
        qty=("quantity", "sum"),
        price=("unit_price", "mean"),
    ).reset_index()
    sensitive_corr = []
    for item_id in price_sensitive_ids[:5]:
        sub = daily_price[daily_price["menu_item_id"] == item_id]
        if len(sub) < 20:
            continue
        corr = sub["price"].corr(sub["qty"])
        sensitive_corr.append(corr)
    if sensitive_corr:
        neg = sum(1 for c in sensitive_corr if pd.notna(c) and c < -0.1)
        check("Price-sensitive items: negative correlation",
              neg >= 1, f"{neg}/{len(sensitive_corr)} with r < -0.1")

    check("SRS channel names used",
          set(orders["order_channel"].unique()).issubset(set([
              "Dine-in", "Takeaway", "Restaurant Website/App",
              "Third-party delivery platforms", "Other supported channels"
          ])))

    print("\n" + "=" * 72)
    print("U5 SELF-TESTS")
    print("=" * 72)
    fails = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        suffix = f"  [{detail}]" if detail else ""
        print(f"[{mark}] {name}{suffix}")
        if not ok:
            fails += 1
    print("=" * 72)
    print(f"RESULT: {len(results) - fails} PASS / {fails} FAIL")
    print("=" * 72)
    return fails == 0


if __name__ == "__main__":
    ok = run_u5_tests()
    raise SystemExit(0 if ok else 1)
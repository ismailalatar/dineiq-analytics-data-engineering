"""U6 self-tests."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig
from data_generator.generators.dimensions import generate_dimensions
from data_generator.generators.pricing import generate_pricing_history
from data_generator.generators.promotions import generate_promotions
from data_generator.generators.orders import generate_orders_and_items
from data_generator.generators.ratings import generate_ratings
from data_generator.generators.inventory import generate_inventory
from data_generator.generators.wastage import generate_wastage


def run_u6_tests() -> bool:
    cfg = GeneratorConfig(
        seed=42,
        n_customers=5_000,
        n_restaurants=20,
        n_categories=10,
        n_menu_items=150,
        n_promotions=30,
        n_orders=10_000,
        n_ratings=100_000,
        n_wastage=50_000,
    )
    rng = np.random.default_rng(cfg.seed)
    state = generate_dimensions(cfg, rng)
    pricing = generate_pricing_history(cfg, rng, state.menu_items)
    promos, promo_items = generate_promotions(cfg, rng, state.menu_items)
    orders, order_items = generate_orders_and_items(cfg, rng, state, pricing, promos, promo_items)

    ratings = generate_ratings(cfg, rng, state)
    inventory = generate_inventory(cfg, rng, state, orders, order_items)
    wastage = generate_wastage(cfg, rng, state, inventory, orders, order_items)

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    # ---- Ratings ----
    check("Ratings count >= 100,000", len(ratings) >= 100_000, f"{len(ratings)}")
    check("rating_value in 1..5", ratings["rating_value"].between(1, 5).all())
    has_anchor = ratings["menu_item_id"].notna() | ratings["restaurant_id"].notna()
    check("Every rating has item or restaurant", has_anchor.all())

    # Rating mean for high-rated vs low-rated items
    r = ratings.dropna(subset=["menu_item_id"]).copy()
    r["menu_item_id"] = pd.to_numeric(r["menu_item_id"], errors="coerce").astype("Int64")
    high_ids = state.menu_items.loc[state.menu_items["_is_high_rated_poor_profit"], "menu_item_id"]
    low_ids = state.menu_items.loc[state.menu_items["_is_low_rated_high_sales"], "menu_item_id"]
    high_mean = r[r["menu_item_id"].isin(high_ids)]["rating_value"].mean()
    low_mean  = r[r["menu_item_id"].isin(low_ids)]["rating_value"].mean()
    check("High-rated items mean > 4.0", high_mean > 4.0, f"{high_mean:.2f}")
    check("Low-rated items mean < 3.0", low_mean < 3.0, f"{low_mean:.2f}")

    # Rating anomalies: concentration
    r["_day"] = pd.to_datetime(r["rating_timestamp"]).dt.normalize()
    grp = r.groupby(["menu_item_id", "_day"]).agg(cnt=("rating_value", "size"),
                                                    mean_r=("rating_value", "mean")).reset_index()
    mean_cnt = grp["cnt"].mean()
    std_cnt = grp["cnt"].std()
    thr = mean_cnt + 5 * std_cnt
    concentration = grp[grp["cnt"] > thr]
    check("Rating concentration anomaly exists", len(concentration) >= 1, f"{len(concentration)}")
    spikes = ((concentration["cnt"] > thr) & (concentration["mean_r"] >= 4.3)).sum()
    drops  = ((concentration["cnt"] > thr) & (concentration["mean_r"] <= 2.2)).sum()
    check("Rating spike anomaly exists", spikes >= 1, f"{spikes}")
    check("Rating drop anomaly exists", drops >= 1, f"{drops}")

    # ---- Inventory ----
    check("Inventory non-empty", len(inventory) > 0, f"{len(inventory)}")
    check("Inventory covers all items",
          inventory["menu_item_id"].nunique() == len(state.menu_items))
    check("Inventory covers all restaurants",
          inventory["restaurant_id"].nunique() == len(state.restaurants))

    # Identity: closing = opening + replenishment - consumption
    identity = (inventory["opening_quantity"]
                + inventory["replenishment_quantity"]
                - inventory["consumption_quantity"]
                - inventory["closing_quantity"]).abs()
    ok_identity = (identity < 0.01).all()
    check("closing = opening + replenishment - consumption", ok_identity)

    # Consumption correlates with actual orders
    oi_merged = order_items.merge(orders[["order_id", "restaurant_id"]], on="order_id", how="left")
    total_orders_qty = oi_merged.groupby("menu_item_id")["quantity"].sum()
    total_consumption = inventory.groupby("menu_item_id")["consumption_quantity"].sum()
    common = total_orders_qty.index.intersection(total_consumption.index)
    corr = total_orders_qty[common].corr(total_consumption[common])
    check("Consumption correlates with orders (r > 0.5)",
          pd.notna(corr) and corr > 0.5, f"r={corr:.3f}")

    # ---- Wastage ----
    check("Wastage count >= 50,000", len(wastage) >= 50_000, f"{len(wastage)}")
    check("Wastage linked to valid items",
          wastage["menu_item_id"].isin(state.menu_items["menu_item_id"]).all())
    check("Wastage linked to valid restaurants",
          wastage["restaurant_id"].isin(state.restaurants["restaurant_id"]).all())
    check("All wastage_reason valid",
          set(wastage["wastage_reason"].unique()).issubset(
              {"spoilage", "expired", "preparation error", "overproduction", "quality issue"}))
    check("Wastage cost > 0", (wastage["wastage_cost"] > 0).all())

    # Impossible wastage
    inv = inventory.copy()
    inv["inventory_date"] = pd.to_datetime(inv["inventory_date"])
    inv = inv.sort_values("inventory_date")
    inv_lookup = inv[["menu_item_id", "restaurant_id", "inventory_date", "closing_quantity"]]
    impossible = 0
    wastage_sorted = wastage.copy()
    wastage_sorted["wastage_date_ts"] = pd.to_datetime(wastage_sorted["wastage_date"])
    for _, row in wastage_sorted.sample(min(5000, len(wastage_sorted)), random_state=0).iterrows():
        sub = inv_lookup[
            (inv_lookup["menu_item_id"] == row["menu_item_id"]) &
            (inv_lookup["restaurant_id"] == row["restaurant_id"]) &
            (inv_lookup["inventory_date"] <= row["wastage_date_ts"])
        ]
        if len(sub) == 0:
            continue
        avail = float(sub["closing_quantity"].iloc[-1])
        if float(row["quantity_wasted"]) > avail:
            impossible += 1
    check("Impossible wastage exists (qty > prior closing)", impossible >= 1, f"{impossible}")

    # ---- Print ----
    print("\n" + "=" * 72)
    print("U6 SELF-TESTS")
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
    ok = run_u6_tests()
    raise SystemExit(0 if ok else 1)
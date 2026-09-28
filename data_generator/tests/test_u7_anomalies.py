"""U7 self-tests — verify all 15 SRS Step 4 cases are present in raw."""
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
from data_generator.anomalies import inject_anomalies


def run_u7_tests() -> bool:
    cfg = GeneratorConfig(
        seed=42,
        n_customers=5_000,
        n_restaurants=20,
        n_categories=10,
        n_menu_items=150,
        n_promotions=30,
        n_orders=10_000,
        n_ratings=50_000,
        n_wastage=20_000,
    )
    rng = np.random.default_rng(cfg.seed)
    state = generate_dimensions(cfg, rng)
    pricing = generate_pricing_history(cfg, rng, state.menu_items)
    promos, promo_items = generate_promotions(cfg, rng, state.menu_items)
    orders, order_items = generate_orders_and_items(cfg, rng, state, pricing, promos, promo_items)
    ratings = generate_ratings(cfg, rng, state)
    inventory = generate_inventory(cfg, rng, state, orders, order_items)
    wastage = generate_wastage(cfg, rng, state, inventory, orders, order_items)

    tables = {
        "Customers": state.customers.copy(),
        "Restaurants": state.restaurants.copy(),
        "Menu_Categories": state.categories.copy(),
        "Menu_Items": state.menu_items.copy(),
        "Pricing_History": pricing.copy(),
        "Promotions": promos.copy(),
        "Promotion_Items": promo_items.copy(),
        "Orders": orders.copy(),
        "Order_Items": order_items.copy(),
        "Ratings": ratings.copy(),
        "Inventory": inventory.copy(),
        "Wastage": wastage.copy(),
    }
    # Baseline counts before injection
    baseline_orders = len(tables["Orders"])
    baseline_lines = len(tables["Order_Items"])

    out = inject_anomalies(cfg, tables, rng)

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    # 1. Missing values
    missing = (
        out["Orders"]["subtotal"].isna().sum() +
        out["Order_Items"]["unit_cost"].isna().sum() +
        out["Menu_Items"]["base_price"].isna().sum() +
        out["Pricing_History"]["unit_price"].isna().sum()
    )
    check("1. Missing values present", missing > 0, f"{int(missing)} cells")

    # 2. Duplicate orders
    dup_orders = int(out["Orders"].duplicated(subset=["order_id"]).sum())
    check("2. Duplicate order_ids present", dup_orders > 0, f"{dup_orders}")

    # 3. Duplicate order lines
    dup_lines = int(out["Order_Items"].duplicated(subset=["order_item_id"]).sum())
    check("3. Duplicate order_item_ids present", dup_lines > 0, f"{dup_lines}")

    # 4. Invalid menu prices (either negative or absurdly large)
    bp = pd.to_numeric(out["Menu_Items"]["base_price"], errors="coerce")
    inv_price = int(((bp <= 0) | (bp > 1000)).sum())
    check("4. Invalid menu prices present", inv_price > 0, f"{inv_price}") 
    # 5. Negative quantities
    neg_qty = int((pd.to_numeric(out["Order_Items"]["quantity"], errors="coerce") < 0).sum())
    check("5. Negative quantities present", neg_qty > 0, f"{neg_qty}")

    # 6. Invalid dates
    inv_dates = int(pd.to_datetime(out["Orders"]["order_timestamp"], errors="coerce").isna().sum())
    check("6. Invalid dates present", inv_dates > 0, f"{inv_dates}")

    # 7. Invalid ratings
    rv = pd.to_numeric(out["Ratings"]["rating_value"], errors="coerce")
    inv_ratings = int(((rv < 1) | (rv > 5)).sum())
    check("7. Invalid ratings present", inv_ratings > 0, f"{inv_ratings}")

    # 8. Missing customer IDs
    miss_cust = int(out["Orders"]["customer_id"].isna().sum())
    check("8. Missing customer IDs present", miss_cust > 0, f"{miss_cust}")

    # 9. Missing menu IDs
    miss_menu = int(out["Order_Items"]["menu_item_id"].isna().sum())
    check("9. Missing menu IDs present", miss_menu > 0, f"{miss_menu}")

    # 10. Invalid restaurant IDs
    valid_rest = set(state.restaurants["restaurant_id"])
    bad_rest = 0
    s = pd.to_numeric(out["Orders"]["restaurant_id"], errors="coerce")
    bad_rest = int((s.notna() & ~s.isin(valid_rest)).sum())
    check("10. Invalid restaurant IDs present", bad_rest > 0, f"{bad_rest}")

    # 11. Impossible wastage (from U6)
    inv2 = out["Inventory"].copy()
    inv2["inventory_date"] = pd.to_datetime(inv2["inventory_date"], errors="coerce")
    inv2 = inv2.sort_values("inventory_date")
    inv_lookup = inv2[["menu_item_id", "restaurant_id", "inventory_date", "closing_quantity"]]
    was2 = out["Wastage"].copy()
    was2["wastage_date"] = pd.to_datetime(was2["wastage_date"], errors="coerce")
    impossible = 0
    for _, row in was2.dropna(subset=["wastage_date"]).sample(min(3000, len(was2)), random_state=0).iterrows():
        sub = inv_lookup[
            (inv_lookup["menu_item_id"] == row["menu_item_id"]) &
            (inv_lookup["restaurant_id"] == row["restaurant_id"]) &
            (inv_lookup["inventory_date"] <= row["wastage_date"])
        ]
        if len(sub) == 0:
            continue
        if float(pd.to_numeric(row["quantity_wasted"], errors="coerce")) > float(sub["closing_quantity"].iloc[-1]):
            impossible += 1
    check("11. Impossible wastage present", impossible > 0, f"{impossible}")

    # 12. Incorrect discounts
    disc = pd.to_numeric(out["Order_Items"]["discount_amount"], errors="coerce")
    gross = (pd.to_numeric(out["Order_Items"]["quantity"], errors="coerce").abs() *
             pd.to_numeric(out["Order_Items"]["unit_price"], errors="coerce").abs())
    bad_disc = int((disc > gross).sum())
    check("12. Incorrect discounts present", bad_disc > 0, f"{bad_disc}")

    # 13. Cancelled transactions
    cancelled = int(out["Orders"]["order_status"].astype(str).str.lower().eq("cancelled").sum())
    check("13. Cancelled transactions present", cancelled > 0, f"{cancelled}")

    # 14. Inconsistent units
    uom_master = state.menu_items.set_index("menu_item_id")["unit_of_measure"].to_dict()
    inv_bad_uom = sum(1 for _, r in out["Inventory"].iterrows()
                      if r["menu_item_id"] in uom_master and pd.notna(r["unit_of_measure"])
                      and r["unit_of_measure"] != uom_master[r["menu_item_id"]])
    was_bad_uom = sum(1 for _, r in out["Wastage"].iterrows()
                      if r["menu_item_id"] in uom_master and pd.notna(r["unit_of_measure"])
                      and r["unit_of_measure"] != uom_master[r["menu_item_id"]])
    check("14. Inconsistent units present",
          inv_bad_uom + was_bad_uom > 0,
          f"Inventory={inv_bad_uom}, Wastage={was_bad_uom}")

    # 15. Invalid location references
    # Orders with restaurant_id not in Restaurants — same as case 10
    check("15. Invalid location references present", bad_rest > 0, f"{bad_rest}")

    # ---- Safety checks (SRS warns not to destroy patterns) ----
    new_orders = len(out["Orders"])
    new_lines = len(out["Order_Items"])
    check("Orders grew by <= 3% (not over-injected)",
          new_orders <= baseline_orders * 1.03,
          f"before={baseline_orders} after={new_orders}")
    check("Order_Items grew by <= 3% (not over-injected)",
          new_lines <= baseline_lines * 1.03,
          f"before={baseline_lines} after={new_lines}")

    # Clean rows should still be a vast majority
    oi = out["Order_Items"]
    clean_lines = (
        oi["quantity"].notna() &
        oi["unit_price"].notna() &
        (pd.to_numeric(oi["quantity"], errors="coerce") > 0) &
        (pd.to_numeric(oi["unit_price"], errors="coerce") > 0)
    ).sum()
    ratio_clean = clean_lines / len(oi)
    check("Clean line ratio >= 0.95", ratio_clean >= 0.95, f"{ratio_clean:.3f}")

    print("\n" + "=" * 72)
    print("U7 SELF-TESTS")
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
    ok = run_u7_tests()
    raise SystemExit(0 if ok else 1)
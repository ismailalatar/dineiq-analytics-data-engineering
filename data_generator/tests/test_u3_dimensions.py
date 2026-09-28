"""U3 self-tests. Runtime only, no file I/O."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig
from data_generator.generators.dimensions import generate_dimensions


def run_u3_tests() -> bool:
    cfg = GeneratorConfig(
        seed=42,
        n_customers=50_000,
        n_restaurants=20,
        n_categories=10,
        n_menu_items=150,
    )
    rng = np.random.default_rng(cfg.seed)
    state = generate_dimensions(cfg, rng)

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    # --- Counts ---
    check("Customers count == 50,000", len(state.customers) == 50_000, f"{len(state.customers)}")
    check("Restaurants count == 20",    len(state.restaurants) == 20, f"{len(state.restaurants)}")
    check("Categories count == 10",     len(state.categories) == 10, f"{len(state.categories)}")
    check("Menu items count == 150",    len(state.menu_items) == 150, f"{len(state.menu_items)}")

    # --- Uniqueness ---
    check("customer_id unique",   state.customers["customer_id"].is_unique)
    check("restaurant_id unique", state.restaurants["restaurant_id"].is_unique)
    check("category_id unique",   state.categories["category_id"].is_unique)
    check("menu_item_id unique",  state.menu_items["menu_item_id"].is_unique)

    # --- Customer date validity ---
    reg = pd.to_datetime(state.customers["registration_date"])
    check("registration_date >= start - 730d",
          (reg >= cfg.start - pd.Timedelta(days=730)).all())
    check("registration_date <= end",
          (reg <= cfg.end).all())

    # --- Segment distribution ---
    seg_counts = state.customers["_segment"].value_counts()
    check("All 5 segments present",
          set(seg_counts.index) == {"new", "churned", "high_value", "frequent", "occasional"},
          dict(seg_counts))

    # --- New customers registered within last 90 days ---
    new_reg = reg[state.customers["_segment"] == "new"]
    check("New customers within last 90 days",
          (new_reg >= cfg.end - pd.Timedelta(days=cfg.new_customer_horizon_days)).all())

    # --- Category integrity ---
    valid_cats = set(state.categories["category_id"].tolist())
    check("All items have valid category_id",
          set(state.menu_items["category_id"].unique()).issubset(valid_cats))

    # --- Flag existence ---
    mi = state.menu_items
    check("Popular items >= 20",            mi["_is_popular"].sum() >= 20,             int(mi["_is_popular"].sum()))
    check("Loss-making items >= 3",         mi["_is_loss_making"].sum() >= 3,          int(mi["_is_loss_making"].sum()))
    check("High-wastage items >= 15",       mi["_is_high_wastage"].sum() >= 15,        int(mi["_is_high_wastage"].sum()))
    check("Profitable-low-selling >= 5",    mi["_is_profitable_low_selling"].sum() >= 5, int(mi["_is_profitable_low_selling"].sum()))
    check("New items >= 5",                 mi["_is_new_item"].sum() >= 5,             int(mi["_is_new_item"].sum()))
    check("Weekend-only >= 3",              mi["_is_weekend_only"].sum() >= 3,         int(mi["_is_weekend_only"].sum()))
    check("Seasonal >= 5",                  mi["_is_seasonal"].sum() >= 5,             int(mi["_is_seasonal"].sum()))
    check("Price-sensitive >= 5",           mi["_is_price_sensitive"].sum() >= 5,      int(mi["_is_price_sensitive"].sum()))
    check("Promo-dependent >= 5",           mi["_is_promo_dependent"].sum() >= 5,      int(mi["_is_promo_dependent"].sum()))

    # --- Forced overlaps ---
    check("Popular + high-wastage >= 3",
          (mi["_is_popular"] & mi["_is_high_wastage"]).sum() >= 3,
          int((mi["_is_popular"] & mi["_is_high_wastage"]).sum()))
    check("Popular + loss-making >= 3",
          (mi["_is_popular"] & mi["_is_loss_making"]).sum() >= 3,
          int((mi["_is_popular"] & mi["_is_loss_making"]).sum()))
    check("Popular + low-margin >= 5",
          (mi["_is_popular"] & mi["_is_low_margin"]).sum() >= 5,
          int((mi["_is_popular"] & mi["_is_low_margin"]).sum()))

    # --- Loss-making arithmetic ---
    loss = mi[mi["_is_loss_making"]]
    check("Loss-making: cost > price",
          (loss["standard_cost"] > loss["base_price"]).all(),
          f"{len(loss)} items")

    # --- Profitable-low-selling margin ---
    prof = mi[mi["_is_profitable_low_selling"]]
    if len(prof) > 0:
        margins = 1 - (prof["standard_cost"] / prof["base_price"])
        check("Profitable-low-selling margin >= 0.55", margins.min() >= 0.55, f"min={margins.min():.2f}")

    # --- New items first_available within last 120 days ---
    new_items = mi[mi["_is_new_item"]]
    if len(new_items) > 0:
        late = (new_items["_first_available_date"] >= cfg.end - pd.Timedelta(days=120)).all()
        check("New items first_available within last 120 days", bool(late))

    # --- Location affinity ---
    check("Location affinity shape (150, 20)",
          state.location_affinity.shape == (150, 20),
          str(state.location_affinity.shape))
    check("Location affinity all positive",
          (state.location_affinity > 0).all())

    # --- Print ---
    print("\n" + "=" * 72)
    print("U3 SELF-TESTS")
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
    ok = run_u3_tests()
    raise SystemExit(0 if ok else 1)
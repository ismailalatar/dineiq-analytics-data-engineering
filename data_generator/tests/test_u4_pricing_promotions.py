"""U4 self-tests."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig
from data_generator.generators.dimensions import generate_dimensions
from data_generator.generators.pricing import generate_pricing_history
from data_generator.generators.promotions import generate_promotions


def run_u4_tests() -> bool:
    cfg = GeneratorConfig(
        seed=42,
        n_customers=2_000,
        n_restaurants=20,
        n_categories=10,
        n_menu_items=150,
        n_promotions=30,
    )
    rng = np.random.default_rng(cfg.seed)
    state = generate_dimensions(cfg, rng)

    pricing = generate_pricing_history(cfg, rng, state.menu_items)
    promotions, promotion_items = generate_promotions(cfg, rng, state.menu_items)

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    # --- Pricing ---
    check("Pricing_History non-empty", len(pricing) > 0, f"{len(pricing)}")

    items_in_pricing = pricing["menu_item_id"].nunique()
    check("Pricing covers every menu item",
          items_in_pricing == cfg.n_menu_items, f"{items_in_pricing}/{cfg.n_menu_items}")

    counts = pricing.groupby("menu_item_id").size()
    check("Each item has >= 3 records", (counts >= 3).all(), f"min={counts.min()}")
    check("Each item has <= 6 records", (counts <= 6).all(), f"max={counts.max()}")

    # Effective dates within item windows
    pricing["effective_date"] = pd.to_datetime(pricing["effective_date"])
    check("All effective_date >= start", (pricing["effective_date"] >= cfg.start).all())
    check("All effective_date <= end", (pricing["effective_date"] <= cfg.end).all())

    # Price changes exist
    merged = pricing.merge(
        state.menu_items[["menu_item_id", "base_price", "standard_cost", "_is_loss_making"]],
        on="menu_item_id", how="left",
    )
    merged = merged.sort_values(["menu_item_id", "effective_date"])
    merged["prev"] = merged.groupby("menu_item_id")["unit_price"].shift(1)
    merged["pct"] = (merged["unit_price"] - merged["prev"]) / merged["prev"]
    big = (merged["pct"].abs() > 0.05).sum()
    check("Meaningful price changes (>5%) exist", big >= 20, f"{big} changes")

    # Loss-making guard
    loss = merged[merged["_is_loss_making"] == True]
    if len(loss) > 0:
        ok = (loss["unit_price"] < loss["standard_cost"]).all()
        check("Loss-making items keep price < cost", ok)

    # --- Promotions ---
    check("Promotions count == 30", len(promotions) == 30, f"{len(promotions)}")
    check("Promotion_ids unique", promotions["promotion_id"].is_unique)

    p_start = pd.to_datetime(promotions["start_date"])
    p_end = pd.to_datetime(promotions["end_date"])
    check("All start_date >= cfg.start", (p_start >= cfg.start).all())
    check("All end_date <= cfg.end", (p_end <= cfg.end).all())
    check("All end_date > start_date", (p_end > p_start).all())

    check("discount_type in {percentage, fixed_amount}",
          set(promotions["discount_type"].unique()).issubset({"percentage", "fixed_amount"}))

    pct = promotions[promotions["discount_type"] == "percentage"]
    check("Percentage discounts in 1..60",
          ((pct["discount_value"] >= 1.0) & (pct["discount_value"] <= 60.0)).all())

    # Coupons
    check("Some promos have coupon_code",
          promotions["coupon_code"].notna().sum() >= 5,
          f"{promotions['coupon_code'].notna().sum()} with coupon")

    # Trap promos exist with heavy discount
    heavy = promotions[(promotions["discount_type"] == "percentage") &
                       (promotions["discount_value"] >= 40.0)]
    check("Heavy-discount (trap) promos exist", len(heavy) >= 5, f"{len(heavy)}")

    # --- Promotion_Items ---
    check("Promotion_Items non-empty", len(promotion_items) > 0, f"{len(promotion_items)}")
    check("All promotion_id in Promotion_Items valid",
          promotion_items["promotion_id"].isin(promotions["promotion_id"]).all())
    check("All menu_item_id in Promotion_Items valid",
          promotion_items["menu_item_id"].isin(state.menu_items["menu_item_id"]).all())
    check("Each promotion has >= 3 items",
          promotion_items.groupby("promotion_id").size().min() >= 3)
    check("No duplicate (promotion_id, menu_item_id) pairs",
          not promotion_items.duplicated(subset=["promotion_id", "menu_item_id"]).any())

    # Trap promos target low-margin items
    low_margin_ids = set(state.menu_items.loc[
        state.menu_items["_is_low_margin"] | state.menu_items["_is_high_rated_poor_profit"],
        "menu_item_id",
    ].tolist())
    trap_promos = promotions.loc[promotions["_is_trap"], "promotion_id"].tolist()
    overlap = 0
    for pid in trap_promos:
        items = set(promotion_items.loc[promotion_items["promotion_id"] == pid, "menu_item_id"].tolist())
        if len(items & low_margin_ids) > 0:
            overlap += 1
    check("Trap promos include low-margin items",
          overlap >= max(1, int(len(trap_promos) * 0.5)),
          f"{overlap}/{len(trap_promos)} traps")

    print("\n" + "=" * 72)
    print("U4 SELF-TESTS")
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
    ok = run_u4_tests()
    raise SystemExit(0 if ok else 1)
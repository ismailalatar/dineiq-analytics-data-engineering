"""
U4 — Promotions + Promotion_Items Generator

Produces campaign headers and their target item lists.
No behavior is generated here — U5 will use these when building orders.

Trap promos: 30% of campaigns get 40-55% discount targeting low-margin items.
The resulting negative contribution margin only appears once U5 applies them.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_promotions(cfg, rng, menu_items: pd.DataFrame):
    n = cfg.n_promotions
    start = cfg.start
    end = cfg.end
    year_days = (end - start).days

    # 30% of campaigns are intended to become traps.
    n_trap = max(1, int(n * 0.30))
    trap_ids = set(int(x) for x in rng.choice(np.arange(1, n + 1), size=n_trap, replace=False))

    # Pools
    low_margin_pool = menu_items.loc[
        menu_items["_is_low_margin"] | menu_items["_is_high_rated_poor_profit"],
        "menu_item_id",
    ].to_numpy(dtype=int)
    promo_dep_pool = menu_items.loc[
        menu_items["_is_promo_dependent"], "menu_item_id"
    ].to_numpy(dtype=int)
    all_items = menu_items["menu_item_id"].to_numpy(dtype=int)

    promo_rows = []
    promo_item_rows = []

    for pid in range(1, n + 1):
        duration = int(rng.integers(20, 45))
        latest_start = max(10, year_days - duration - 5)
        offset = int(rng.integers(10, latest_start))
        p_start = (start + pd.Timedelta(days=offset)).date()
        p_end = (start + pd.Timedelta(days=offset + duration)).date()

        is_trap = pid in trap_ids

        if is_trap:
            dtype = "percentage"
            # 40-55% discount (stored as percentage points).
            dvalue = round(float(rng.uniform(40.0, 55.0)), 2)
            pool = low_margin_pool if len(low_margin_pool) >= 3 else all_items
            n_items = int(rng.integers(3, 7))
        else:
            dtype = rng.choice(["percentage", "fixed_amount"], p=[0.80, 0.20])
            if dtype == "percentage":
                dvalue = round(float(rng.uniform(8.0, 25.0)), 2)
            else:
                dvalue = round(float(rng.uniform(1.0, 8.0)), 2)
            if len(promo_dep_pool) >= 3 and rng.random() < 0.60:
                pool = promo_dep_pool
            else:
                pool = all_items
            n_items = int(rng.integers(4, 10))

        n_items = min(n_items, len(pool))
        chosen = rng.choice(pool, size=n_items, replace=False)

        coupon = f"DINEIQ{pid:03d}" if rng.random() < 0.40 else None

        promo_rows.append({
            "promotion_id": pid,
            "promotion_name": f"Campaign {pid:02d}",
            "discount_type": dtype,
            "discount_value": dvalue,
            "coupon_code": coupon,
            "start_date": p_start,
            "end_date": p_end,
            "_is_trap": is_trap,
        })

        for mi in chosen:
            promo_item_rows.append({
                "promotion_id": pid,
                "menu_item_id": int(mi),
            })

    promotions = pd.DataFrame(promo_rows, columns=[
        "promotion_id", "promotion_name", "discount_type", "discount_value",
        "coupon_code", "start_date", "end_date", "_is_trap",
    ])
    promotion_items = pd.DataFrame(promo_item_rows, columns=[
        "promotion_id", "menu_item_id",
    ])
    return promotions, promotion_items
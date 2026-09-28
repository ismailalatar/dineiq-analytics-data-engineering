"""
U6 — Wastage Generator

Produces 50,000 wastage records.
High-wastage items get more weight.
A small fraction (2%) are made impossible:
quantity_wasted > most recent prior closing_quantity for that (item, restaurant).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


REASONS = ["spoilage", "expired", "preparation error", "overproduction", "quality issue"]
REASON_PROBS = [0.30, 0.20, 0.20, 0.20, 0.10]


def generate_wastage(cfg, rng, state, inventory, orders, order_items) -> pd.DataFrame:
    n = int(cfg.n_wastage)
    start = cfg.start
    end = cfg.end
    n_days = (end - start).days + 1

    menu = state.menu_items
    item_ids = menu["menu_item_id"].to_numpy(dtype=int)
    n_items = len(item_ids)
    costs = menu["standard_cost"].to_numpy(dtype=float)
    uoms = menu["unit_of_measure"].to_numpy()
    is_high_waste = menu["_is_high_wastage"].to_numpy()

    w = np.where(is_high_waste, 7.0, 1.0)
    w = w / w.sum()

    chosen_items = rng.choice(item_ids, size=n, p=w)
    rest_ids = state.restaurants["restaurant_id"].to_numpy(dtype=int)
    chosen_rest = rng.choice(rest_ids, size=n)
    day_offsets = rng.integers(0, n_days, size=n)
    chosen_dates = pd.to_datetime(start) + pd.to_timedelta(day_offsets, unit="D")

    base_qty = rng.uniform(0.25, 8.0, size=n)
    base_qty = np.where(is_high_waste[chosen_items - 1], base_qty * 2.5, base_qty)
    cost_per_unit = costs[chosen_items - 1]
    wastage_cost = np.round(base_qty * cost_per_unit, 2)

    reasons = rng.choice(REASONS, size=n, p=REASON_PROBS)

    df = pd.DataFrame({
        "wastage_id": np.arange(1, n + 1, dtype=np.int64),
        "menu_item_id": chosen_items.astype(np.int64),
        "restaurant_id": chosen_rest.astype(np.int64),
        "wastage_date": chosen_dates.date,
        "quantity_wasted": np.round(base_qty, 3),
        "unit_of_measure": uoms[chosen_items - 1],
        "wastage_cost": wastage_cost,
        "wastage_reason": reasons,
    })

    # Impossible wastage: 2% forced to exceed the last known closing quantity.
    inv = inventory.copy()
    inv["inventory_date"] = pd.to_datetime(inv["inventory_date"])
    inv = inv.sort_values("inventory_date")
    inv_lookup = inv[["menu_item_id", "restaurant_id", "inventory_date", "closing_quantity"]]

    n_imp = max(1, int(n * 0.02))
    imp_idx = rng.choice(n, size=n_imp, replace=False)

    df["wastage_date_ts"] = pd.to_datetime(df["wastage_date"])
    for i in imp_idx:
        item_id = int(df.at[i, "menu_item_id"])
        rest_id = int(df.at[i, "restaurant_id"])
        wdate = df.at[i, "wastage_date_ts"]
        sub = inv_lookup[
            (inv_lookup["menu_item_id"] == item_id) &
            (inv_lookup["restaurant_id"] == rest_id) &
            (inv_lookup["inventory_date"] <= wdate)
        ]
        if len(sub) == 0:
            continue
        avail = float(sub["closing_quantity"].iloc[-1])
        new_qty = round(avail + float(rng.uniform(3.0, 15.0)), 3)
        df.at[i, "quantity_wasted"] = new_qty
        df.at[i, "wastage_cost"] = round(new_qty * cost_per_unit[i], 2)

    df = df.drop(columns=["wastage_date_ts"])
    return df
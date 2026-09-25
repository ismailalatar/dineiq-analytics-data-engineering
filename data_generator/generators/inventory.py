"""
U6 — Inventory Generator

Weekly snapshots per (menu_item, restaurant). Consumption is the sum of
that week's order quantities for the same pair, so inventory usage is
directly derived from actual sales activity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_inventory(cfg, rng, state, orders, order_items) -> pd.DataFrame:
    start = cfg.start
    end = cfg.end
    n_weeks = ((end - start).days // 7) + 1

    week_starts = pd.date_range(start, periods=n_weeks, freq="7D")

    # Consumption per (item, restaurant, week)
    oi = order_items.merge(
        orders[["order_id", "restaurant_id", "order_timestamp"]],
        on="order_id", how="left",
    )
    oi["order_date"] = pd.to_datetime(oi["order_timestamp"]).dt.normalize()
    week_idx = ((oi["order_date"] - start).dt.days // 7).astype(int)
    week_idx = week_idx.clip(lower=0, upper=n_weeks - 1)
    oi["_week_idx"] = week_idx

    daily = oi.groupby(["restaurant_id", "menu_item_id", "_week_idx"])["quantity"].sum().reset_index()

    consumption_map = {
        (int(r), int(m), int(w)): float(q)
        for r, m, w, q in daily.itertuples(index=False)
    }

    uom_map = state.menu_items.set_index("menu_item_id")["unit_of_measure"].to_dict()

    rows = []
    inv_id = 1
    restaurant_ids = state.restaurants["restaurant_id"].to_numpy(dtype=int)
    item_ids = state.menu_items["menu_item_id"].to_numpy(dtype=int)

    for r in restaurant_ids:
        for m in item_ids:
            current_stock = float(rng.uniform(40.0, 200.0))
            for w in range(n_weeks):
                key = (int(r), int(m), int(w))
                cons = consumption_market_get(consumption_map, key, rng)
                replen = cons * float(rng.uniform(0.7, 1.3)) + float(rng.uniform(2, 12))
                opening = max(0.0, current_stock)
                closing = max(0.0, opening + replen - cons)
                rows.append({
                    "inventory_id": inv_id,
                    "menu_item_id": int(m),
                    "restaurant_id": int(r),
                    "inventory_date": week_starts[w].date(),
                    "opening_quantity": round(opening, 3),
                    "replenishment_quantity": round(replen, 3),
                    "consumption_quantity": round(cons, 3),
                    "closing_quantity": round(closing, 3),
                    "unit_of_measure": uom_map.get(int(m), "portion"),
                })
                inv_id += 1
                current_stock = closing

    return pd.DataFrame(rows)


def consumption_market_get(consumption_map, key, rng):
    """Return the week's consumption; if no sales, return 0 (no fake consumption)."""
    return consumption_map.get(key, 0.0)
"""
U4 — Pricing History Generator

Produces historical price records for every menu item.
No cost column — SRS FR v mentions price changes only.
Loss-making items keep unit_price < standard_cost across all records.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_pricing_history(cfg, rng, menu_items: pd.DataFrame) -> pd.DataFrame:
    rows = []
    pid = 1

    for _, item in menu_items.iterrows():
        first_avail = pd.Timestamp(item["_first_available_date"])
        end = cfg.end

        window_start = max(cfg.start, first_avail)
        total_days = max(1, (end - window_start).days)

        # 3-6 records per item; first record lands at item's launch.
        n_records = int(rng.integers(cfg.min_prices_per_item, cfg.max_prices_per_item + 1))
        n_records = min(n_records, total_days + 1)

        offsets = np.sort(rng.choice(np.arange(0, total_days + 1), size=n_records, replace=False))
        offsets[0] = 0
        dates = window_start + pd.to_timedelta(offsets, unit="D")

        base_price = float(item["base_price"])
        cost = float(item["standard_cost"])
        is_loss_making = bool(item.get("_is_loss_making", False))
        is_sensitive = bool(item.get("_is_price_sensitive", False))

        # Price-sensitive items drift more so price-demand signals are visible later.
        drift_scale = 0.18 if is_sensitive else 0.04

        current_price = base_price
        for i, d in enumerate(dates):
            if i > 0:
                drift = rng.normal(0.0, drift_scale)
                current_price = max(0.5, round(current_price * (1 + drift), 2))

            # Loss-making property must hold across every effective period.
            if is_loss_making and current_price >= cost:
                current_price = round(cost * float(rng.uniform(0.85, 0.95)), 2)

            rows.append({
                "pricing_history_id": pid,
                "menu_item_id": int(item["menu_item_id"]),
                "effective_date": d.date(),
                "unit_price": current_price,
            })
            pid += 1

    return pd.DataFrame(rows, columns=[
        "pricing_history_id", "menu_item_id", "effective_date", "unit_price",
    ])
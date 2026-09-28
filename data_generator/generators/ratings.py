"""
U6 — Ratings Generator

Produces item-level and/or restaurant-level ratings.
Rating mean varies by item flag so that:
  - _is_high_rated_poor_profit items have mean ~4.5
  - _is_low_rated_high_sales items have mean ~2.1
Anomaly clusters create: sudden spikes, sudden drops, high concentration.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_ratings(cfg, rng, state) -> pd.DataFrame:
    n = int(cfg.n_ratings)
    menu = state.menu_items
    n_days = (cfg.end - cfg.start).days + 1

    item_ids = menu["menu_item_id"].to_numpy(dtype=int)
    item_uom_mean = np.full(len(menu), 3.8, dtype=float)
    item_uom_mean[menu["_is_high_rated_poor_profit"].to_numpy()] = 4.5
    item_uom_mean[menu["_is_low_rated_high_sales"].to_numpy()] = 2.1

    rest_ids = state.restaurants["restaurant_id"].to_numpy(dtype=int)
    cust_ids = state.customers["customer_id"].to_numpy(dtype=int)

    # ---- Row composition ----
    # 0 = item-only, 1 = restaurant-only, 2 = both
    modes = rng.choice([0, 1, 2], size=n, p=[0.55, 0.15, 0.30])
    item_choice = rng.choice(item_ids, size=n)
    rest_choice = rng.choice(rest_ids, size=n)

    menu_id = np.full(n, -1, dtype=np.int64)
    rest_id = np.full(n, -1, dtype=np.int64)
    item_mask = modes != 1
    rest_mask = modes != 0
    menu_id[item_mask] = item_choice[item_mask]
    rest_id[rest_mask] = rest_choice[rest_mask]

    # ---- Value generation ----
    means = np.full(n, 3.8, dtype=float)
    idx = menu_id[item_mask] - 1
    means[item_mask] = item_uom_mean[idx]
    values = np.clip(np.rint(rng.normal(means, 0.75)), 1, 5).astype(int)

    # ---- Customer assignment (nullable per D31 Raw policy) ----
    customer_id = np.full(n, -1, dtype=np.int64)
    with_customer = rng.random(n) < 0.70
    customer_id[with_customer] = rng.choice(cust_ids, size=int(with_customer.sum()))

    # ---- Timestamps ----
    day_offsets = rng.integers(0, n_days, size=n)
    hours = rng.integers(8, 23, size=n)
    minutes = rng.integers(0, 60, size=n)
    timestamps = (
        np.datetime64(cfg.start, "ns")
        + day_offsets.astype("timedelta64[D]")
        + hours.astype("timedelta64[h]")
        + minutes.astype("timedelta64[m]")
    )

    df = pd.DataFrame({
    "rating_id": np.arange(1, n + 1, dtype=np.int64),
    "customer_id": pd.array(customer_id, dtype="Int64"),
    "menu_item_id": pd.array(menu_id, dtype="Int64"),
    "restaurant_id": pd.array(rest_id, dtype="Int64"),
    "rating_value": values,
    "rating_timestamp": pd.to_datetime(timestamps),
})

    # Replace -1 with NA
    df.loc[df["customer_id"] == -1, "customer_id"] = pd.NA
    df.loc[df["menu_item_id"] == -1, "menu_item_id"] = pd.NA
    df.loc[df["restaurant_id"] == -1, "restaurant_id"] = pd.NA

    # ---- Anomaly clusters (2 spike / 2 drop / 2 concentration) ----
    cluster_rows = []

    # 2 sudden spikes: 60-90 ratings of 4-5 for one item in 1-2 days
    for _ in range(2):
        mi = int(rng.choice(item_ids))
        start_day = int(rng.integers(30, n_days - 30))
        cluster_n = int(rng.integers(60, 90))
        day_offsets = rng.integers(0, 2, size=cluster_n)
        ts = (
            np.datetime64(cfg.start, "ns")
            + (start_day + day_offsets).astype("timedelta64[D]")
            + rng.integers(0, 24 * 60, size=cluster_n).astype("timedelta64[m]")
        )
        cluster_rows.append(pd.DataFrame({
            "customer_id": pd.NA,
            "menu_item_id": mi,
            "restaurant_id": pd.NA,
            "rating_value": rng.choice([4, 5], size=cluster_n, p=[0.3, 0.7]),
            "rating_timestamp": pd.to_datetime(ts),
        }))

    # 2 sudden drops: 60-90 ratings of 1-2 for one item in 1-2 days
    for _ in range(2):
        mi = int(rng.choice(item_ids))
        start_day = int(rng.integers(30, n_days - 30))
        cluster_n = int(rng.integers(60, 90))
        day_offsets = rng.integers(0, 2, size=cluster_n)
        ts = (
            np.datetime64(cfg.start, "ns")
            + (start_day + day_offsets).astype("timedelta64[D]")
            + rng.integers(0, 24 * 60, size=cluster_n).astype("timedelta64[m]")
        )
        cluster_rows.append(pd.DataFrame({
            "customer_id": pd.NA,
            "menu_item_id": mi,
            "restaurant_id": pd.NA,
            "rating_value": rng.choice([1, 2], size=cluster_n, p=[0.7, 0.3]),
            "rating_timestamp": pd.to_datetime(ts),
        }))

    # 2 concentrated: 80-120 ratings on a single day for one item
    for _ in range(2):
        mi = int(rng.choice(item_ids))
        day = int(rng.integers(30, n_days - 30))
        cluster_n = int(rng.integers(80, 120))
        ts = (
            np.datetime64(cfg.start, "ns")
            + np.full(cluster_n, day).astype("timedelta64[D]")
            + rng.integers(0, 24 * 60, size=cluster_n).astype("timedelta64[m]")
        )
        cluster_rows.append(pd.DataFrame({
            "customer_id": pd.NA,
            "menu_item_id": mi,
            "restaurant_id": pd.NA,
            "rating_value": rng.integers(1, 6, size=cluster_n),
            "rating_timestamp": pd.to_datetime(ts),
        }))

    if cluster_rows:
        cluster_df = pd.concat(cluster_rows, ignore_index=True)
        cluster_df["rating_id"] = np.arange(len(df) + 1, len(df) + 1 + len(cluster_df), dtype=np.int64)
        cluster_df = cluster_df[["rating_id", "customer_id", "menu_item_id",
                                  "restaurant_id", "rating_value", "rating_timestamp"]]
        df = pd.concat([df, cluster_df], ignore_index=True)

    return df
from __future__ import annotations

import numpy as np
import pandas as pd


def _pick_idx(df, rate, rng):
    n = max(1, int(len(df) * rate))
    return rng.choice(df.index.to_numpy(), size=min(n, len(df)), replace=False)


def inject_anomalies(cfg, tables, rng):
    out = {k: v.copy() for k, v in tables.items()}

    n = int(len(out["Orders"]) * cfg.duplicate_order_rate)
    if n > 0:
        idx = rng.choice(out["Orders"].index.to_numpy(), size=n, replace=False)
        out["Orders"] = pd.concat(
            [out["Orders"], out["Orders"].loc[idx].copy()], ignore_index=True,
        )

    n = int(len(out["Order_Items"]) * cfg.duplicate_order_item_rate)
    if n > 0:
        idx = rng.choice(out["Order_Items"].index.to_numpy(), size=n, replace=False)
        out["Order_Items"] = pd.concat(
            [out["Order_Items"], out["Order_Items"].loc[idx].copy()], ignore_index=True,
        )

    df = out["Orders"]
    df["customer_id"] = df["customer_id"].astype(object)
    idx = _pick_idx(df, cfg.missing_id_rate, rng)
    df.loc[idx, "customer_id"] = None
    out["Orders"] = df

    df = out["Order_Items"]
    df["menu_item_id"] = df["menu_item_id"].astype(object)
    idx = _pick_idx(df, cfg.missing_id_rate, rng)
    df.loc[idx, "menu_item_id"] = None
    out["Order_Items"] = df

    df = out["Orders"]
    df["restaurant_id"] = df["restaurant_id"].astype(object)
    idx = _pick_idx(df, cfg.invalid_id_rate, rng)
    df.loc[idx, "restaurant_id"] = -999
    out["Orders"] = df

    missing_targets = [
        ("Orders", ["subtotal", "discount_total", "total_amount"]),
        ("Order_Items", ["unit_cost"]),
        ("Menu_Items", ["base_price"]),
        ("Pricing_History", ["unit_price"]),
        ("Wastage", ["wastage_reason"]),
    ]
    for table, cols in missing_targets:
        df = out[table]
        for col in cols:
            df[col] = df[col].astype(object)
            idx = _pick_idx(df, cfg.missing_value_rate, rng)
            df.loc[idx, col] = None
        out[table] = df

    for table, col in [("Order_Items", "quantity"), ("Inventory", "consumption_quantity")]:
        df = out[table]
        df[col] = pd.to_numeric(df[col], errors="coerce")
        idx = _pick_idx(df, cfg.negative_quantity_rate, rng)
        df.loc[idx, col] = -df.loc[idx, col].abs()
        out[table] = df

    for table, col in [
        ("Order_Items", "unit_price"),
        ("Menu_Items", "base_price"),
        ("Pricing_History", "unit_price"),
    ]:
        df = out[table]
        df[col] = pd.to_numeric(df[col], errors="coerce")
        idx = _pick_idx(df, cfg.invalid_price_rate, rng)
        half = len(idx) // 2
        df.loc[idx[:half], col] = -10.0
        df.loc[idx[half:], col] = 99999.99
        out[table] = df

    for table, col in [
        ("Orders", "order_timestamp"),
        ("Ratings", "rating_timestamp"),
        ("Wastage", "wastage_date"),
    ]:
        df = out[table]
        df[col] = pd.to_datetime(df[col], errors="coerce")
        idx = _pick_idx(df, cfg.invalid_date_rate, rng)
        half = len(idx) // 2
        df.loc[idx[:half], col] = pd.NaT
        df.loc[idx[half:], col] = pd.Timestamp("2099-12-31")
        out[table] = df

    df = out["Ratings"]
    df["rating_value"] = pd.to_numeric(df["rating_value"], errors="coerce")
    idx = _pick_idx(df, cfg.invalid_rating_rate, rng)
    df.loc[idx, "rating_value"] = rng.choice([0, -1, 6, 10, 100], size=len(idx))
    out["Ratings"] = df

    df = out["Order_Items"]
    df["discount_amount"] = pd.to_numeric(df["discount_amount"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["line_total"] = pd.to_numeric(df["line_total"], errors="coerce")
    idx = _pick_idx(df, cfg.incorrect_discount_rate, rng)
    gross = df.loc[idx, "quantity"].abs() * df.loc[idx, "unit_price"].abs()
    df.loc[idx, "discount_amount"] = (gross + rng.uniform(5, 20, size=len(idx))).round(2)
    df.loc[idx, "line_total"] = (gross - df.loc[idx, "discount_amount"]).round(2)
    out["Order_Items"] = df

    for table in ["Inventory", "Wastage"]:
        df = out[table]
        df["unit_of_measure"] = df["unit_of_measure"].astype(object)
        idx = _pick_idx(df, cfg.inconsistent_unit_rate, rng)
        df.loc[idx, "unit_of_measure"] = rng.choice(
            ["kg", "liter", "gram", "ml", "box"], size=len(idx),
        )
        out[table] = df

    return out
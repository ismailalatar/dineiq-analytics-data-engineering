from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .config import GeneratorConfig
from .generators import (
    generate_dimensions,
    generate_pricing_history,
    generate_promotions,
    generate_orders_and_items,
    generate_ratings,
    generate_inventory,
    generate_wastage,
)
from .anomalies import inject_anomalies
from .validation import validate_dataset, save_validation_report


def _strip_helpers(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")


def _save_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _save_parquet(df: pd.DataFrame, path: Path) -> bool:
    try:
        df_out = df.copy()
        df_out.attrs = {}
        path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_parquet(path, index=False)
        return True
    except Exception:
        return False


def generate_dataset(cfg: GeneratorConfig = None, run_validation_flag: bool = True):
    cfg = cfg or GeneratorConfig()
    cfg.ensure_output_dirs()

    rng = np.random.default_rng(cfg.seed)
    t0 = time.time()

    print("[1/7] Dimensions ...")
    state = generate_dimensions(cfg, rng)

    print("[2/7] Pricing History ...")
    pricing = generate_pricing_history(cfg, rng, state.menu_items)

    print("[3/7] Promotions ...")
    promos, promo_items = generate_promotions(cfg, rng, state.menu_items)

    print("[4/7] Orders + Order_Items ...")
    orders, order_items = generate_orders_and_items(
        cfg, rng, state, pricing, promos, promo_items,
    )

    print("[5/7] Ratings ...")
    ratings = generate_ratings(cfg, rng, state)

    print("[6/7] Inventory ...")
    inventory = generate_inventory(cfg, rng, state, orders, order_items)

    print("[7/7] Wastage ...")
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

    print("[anomalies] Injecting raw-data defects ...")
    tables = inject_anomalies(cfg, tables, rng)

    print("[save] Writing CSV + Parquet ...")
    raw_dir = cfg.output_dir / "raw_data"
    pq_dir = cfg.output_dir / "parquet_data"
    stats = {}
    for name, df in tables.items():
        clean = _strip_helpers(df)
        _save_csv(clean, raw_dir / f"{name}.csv")
        pq_ok = _save_parquet(clean, pq_dir / f"{name}.parquet")
        stats[name] = {"rows": int(len(clean)), "columns": list(clean.columns), "parquet": pq_ok}
        print(f"  - {name:<18} {len(clean):>10,} rows")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Seed={cfg.seed}.")

    validation = None
    if run_validation_flag:
        validation = validate_dataset(tables, cfg)
        reports_dir = cfg.output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        save_validation_report(validation, reports_dir / "data_generation_validation.json")
        (reports_dir / "dataset_statistics.json").write_text(
            json.dumps(stats, indent=2, default=str), encoding="utf-8",
        )

    return tables, validation
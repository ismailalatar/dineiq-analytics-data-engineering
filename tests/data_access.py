"""Shared, pytest-free helpers for locating and loading DineIQ tables.

Used by the pytest suite (conftest.py) and by the evidence tools, so the same
file-discovery rules apply everywhere. The generator writes
<DATA_DIR>/raw_data/<Table>.csv and <DATA_DIR>/parquet_data/<Table>.parquet.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

# Override with DINEIQ_DATA_DIR, e.g. a hidden-data rehearsal folder.
DATA_DIR = Path(os.environ.get("DINEIQ_DATA_DIR", REPO_ROOT / "full_output"))
RAW_DIR = DATA_DIR / "raw_data"
PARQUET_DIR = DATA_DIR / "parquet_data"
CLEAN_DIR = DATA_DIR / "processed_data" / "clean"

TABLES = [
    "Customers", "Restaurants", "Menu_Categories", "Menu_Items", "Pricing_History",
    "Promotions", "Promotion_Items", "Orders", "Order_Items", "Ratings", "Inventory", "Wastage",
]

# Columns from documentation/data_dictionary/DATA_DICTIONARY.md, plus Menu_Items.launch_date,
# which the generator writes (dimensions.py) but the dictionary does not list yet.
EXPECTED_COLUMNS = {
    "Customers": ["customer_id", "registration_date"],
    "Restaurants": ["restaurant_id", "restaurant_name", "city"],
    "Menu_Categories": ["category_id", "category_name"],
    "Menu_Items": ["menu_item_id", "category_id", "item_name", "description", "base_price",
                   "standard_cost", "availability", "unit_of_measure", "launch_date"],
    "Pricing_History": ["pricing_history_id", "menu_item_id", "effective_date", "unit_price"],
    "Promotions": ["promotion_id", "promotion_name", "discount_type", "discount_value",
                   "coupon_code", "start_date", "end_date"],
    "Promotion_Items": ["promotion_id", "menu_item_id"],
    "Orders": ["order_id", "customer_id", "restaurant_id", "promotion_id", "order_timestamp",
               "order_channel", "order_status", "subtotal", "discount_total", "total_amount"],
    "Order_Items": ["order_item_id", "order_id", "menu_item_id", "quantity", "unit_price",
                    "unit_cost", "discount_amount", "line_total"],
    "Ratings": ["rating_id", "customer_id", "menu_item_id", "restaurant_id", "rating_value",
                "rating_timestamp"],
    "Inventory": ["inventory_id", "menu_item_id", "restaurant_id", "inventory_date",
                  "opening_quantity", "replenishment_quantity", "consumption_quantity",
                  "closing_quantity", "unit_of_measure"],
    "Wastage": ["wastage_id", "menu_item_id", "restaurant_id", "wastage_date", "quantity_wasted",
                "unit_of_measure", "wastage_cost", "wastage_reason"],
}

PRIMARY_KEYS = {
    "Customers": "customer_id", "Restaurants": "restaurant_id", "Menu_Categories": "category_id",
    "Menu_Items": "menu_item_id", "Pricing_History": "pricing_history_id",
    "Promotions": "promotion_id", "Orders": "order_id", "Order_Items": "order_item_id",
    "Ratings": "rating_id", "Inventory": "inventory_id", "Wastage": "wastage_id",
}

_SUFFIX = {"csv": ".csv", "parquet": ".parquet"}


def find_table_path(folder: Path, table: str, suffix: str) -> Path | None:
    """Find a table as `<table><suffix>` (file) or as a Spark output directory named
    `<table>` or `<table><suffix>`, ignoring case. Returns None when nothing matches."""
    if not folder.is_dir():
        return None
    wanted = table.lower()
    for path in sorted(folder.iterdir()):
        name = path.name.lower()
        if name.endswith(suffix):
            name = name[: -len(suffix)]
        elif not path.is_dir():
            continue
        if name == wanted:
            return path
    return None


def read_table(folder: Path, table: str, formats=("csv",), nrows: int | None = None) -> pd.DataFrame:
    """Load a table from the first matching format. Column names are lower-cased."""
    for fmt in formats:
        path = find_table_path(folder, table, _SUFFIX[fmt])
        if path is None:
            continue
        if fmt == "parquet":
            df = pd.read_parquet(path)
        elif path.is_dir():  # Spark writes CSV as a folder of part files
            parts = sorted(path.glob("*.csv"))
            df = pd.concat((pd.read_csv(p, low_memory=False) for p in parts), ignore_index=True)
        else:
            df = pd.read_csv(path, low_memory=False, nrows=nrows)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df.head(nrows) if nrows else df
    raise FileNotFoundError(f"Table '{table}' not found in {folder} (formats tried: {formats})")


def num(series: pd.Series) -> pd.Series:
    """Numeric view of a column; unparseable values become NaN."""
    return pd.to_numeric(series, errors="coerce")


def ts(series: pd.Series) -> pd.Series:
    """Datetime view of a column; unparseable values become NaT (timezone dropped)."""
    out = pd.to_datetime(series, errors="coerce", format="mixed")
    if getattr(out.dt, "tz", None) is not None:
        out = out.dt.tz_localize(None)
    return out


def plausible_dates(t: pd.Series) -> pd.Series:
    """True for real dates: not missing, not in the future (the generator injects
    2099-12-31) and not before 2000."""
    return t.notna() & (t <= pd.Timestamp.now()) & (t.dt.year >= 2000)


def orphan_mask(child_ids: pd.Series, parent_ids: pd.Series) -> pd.Series:
    """True where a non-null (numeric) child key has no matching parent key."""
    child = num(child_ids)
    return child.notna() & ~child.isin(set(num(parent_ids).dropna()))

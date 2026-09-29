"""Independent pandas detectors for the 15 data-quality defect types in SRS Step 4.

They do not replace the Spark data-quality engine in spark_jobs/. They give a
second, independent count that is compared with the Spark report as evidence.
Definitions follow how data_generator/anomalies.py and generators/wastage.py
inject each defect.

Standalone run (from the repo root):
    python -m tests.quality_checks [--out reports/evidence/independent_quality_counts.json]
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from .data_access import (DATA_DIR, RAW_DIR, REPO_ROOT, num, orphan_mask, plausible_dates,
                          read_table, ts)

VALID_UNITS = {"portion", "plate", "bowl", "glass", "piece"}

DEFINITIONS = {
    "missing_values": "Orders (except optional promotion_id) or Order_Items rows with any blank field",
    "duplicate_orders": "Orders repeating an order_id or all non-key fields",
    "duplicate_order_lines": "Order_Items repeating an order_item_id or all non-key fields",
    "invalid_menu_prices": "Prices <= 0 or > 50x the table median (menu, order lines, pricing history)",
    "negative_quantities": "Order_Items.quantity < 0 plus Inventory.consumption_quantity < 0",
    "invalid_dates": "Blank, future or pre-2000 dates in Orders, Ratings and Wastage",
    "invalid_ratings": "Non-blank rating_value outside the whole numbers 1-5",
    "missing_customer_ids": "Orders with blank customer_id",
    "missing_menu_ids": "Order_Items with blank menu_item_id",
    "invalid_restaurant_ids": "Orders whose restaurant_id is not in Restaurants",
    "impossible_wastage": "Negative wastage, or wastage above the latest prior closing stock "
                          "for the same item and location",
    "incorrect_discounts": "Line discount < 0 or > quantity x unit_price, or order discount > subtotal",
    "cancelled_transactions": "Orders with order_status = cancelled",
    "inconsistent_units": "Inventory/Wastage units that differ from the menu item's unit "
                          "or are not portion/plate/bowl/glass/piece",
    "invalid_location_references": "restaurant_id values not in Restaurants, across Orders, "
                                   "Ratings, Inventory and Wastage",
}
DEFECT_TYPES = list(DEFINITIONS)


def _duplicates(df: pd.DataFrame, id_col: str) -> int:
    """Rows repeated either by primary key or by every non-key column."""
    by_id = int(df[id_col].duplicated().sum())
    by_content = int(df.duplicated(subset=[c for c in df.columns if c != id_col]).sum())
    return max(by_id, by_content)


def _bad_price(series: pd.Series) -> pd.Series:
    price = num(series)
    return (price <= 0) | (price > 50 * price[price > 0].median())


def _bad_dates(series: pd.Series) -> pd.Series:
    return ~plausible_dates(ts(series))


def _impossible_wastage(wastage: pd.DataFrame, inventory: pd.DataFrame) -> int:
    stock = pd.DataFrame({
        "m": num(inventory["menu_item_id"]), "r": num(inventory["restaurant_id"]),
        "d": ts(inventory["inventory_date"]), "closing": num(inventory["closing_quantity"]),
    }).dropna(subset=["m", "r", "d"]).sort_values("d")
    w = pd.DataFrame({
        "m": num(wastage["menu_item_id"]), "r": num(wastage["restaurant_id"]),
        "d": ts(wastage["wastage_date"]), "q": num(wastage["quantity_wasted"]),
    })
    negative = int((w["q"] < 0).sum())
    dated = w.dropna(subset=["m", "r", "d"]).sort_values("d")
    matched = pd.merge_asof(dated, stock, on="d", by=["m", "r"], direction="backward")
    exceeds = int(((matched["q"] >= 0) & (matched["q"] > matched["closing"])).sum())
    return negative + exceeds


def _unit_mismatch(df: pd.DataFrame, unit_by_item: pd.Series) -> pd.Series:
    unit = df["unit_of_measure"].astype(str).str.strip()
    expected = num(df["menu_item_id"]).map(unit_by_item)
    return (expected.notna() & (unit != expected)) | ~unit.str.lower().isin(VALID_UNITS)


def detect(load) -> dict:
    """`load(table)` returns a DataFrame. Result: {defect: {"count": n, "rows_checked": n}}."""
    orders, lines = load("Orders"), load("Order_Items")
    menu, restaurants, pricing = load("Menu_Items"), load("Restaurants"), load("Pricing_History")
    ratings, inventory, wastage = load("Ratings"), load("Inventory"), load("Wastage")

    qty, price, disc = num(lines["quantity"]), num(lines["unit_price"]), num(lines["discount_amount"])
    rating = num(ratings["rating_value"])
    rest_ids = restaurants["restaurant_id"]

    unit_by_item = pd.Series(menu["unit_of_measure"].astype(str).str.strip().values,
                             index=num(menu["menu_item_id"]))
    unit_by_item = unit_by_item[~unit_by_item.index.duplicated()]

    required_header = [c for c in orders.columns if c != "promotion_id"]  # promotion is optional
    bad_line_discount = (disc < 0) | ((qty > 0) & (price > 0) & (disc > qty * price + 0.01))
    bad_order_discount = num(orders["discount_total"]) > num(orders["subtotal"]) + 0.01
    location_orphans = sum(int(orphan_mask(t["restaurant_id"], rest_ids).sum())
                           for t in (orders, ratings, inventory, wastage))

    counts = {
        "missing_values": (orders[required_header].isna().any(axis=1).sum()
                           + lines.isna().any(axis=1).sum(), len(orders) + len(lines)),
        "duplicate_orders": (_duplicates(orders, "order_id"), len(orders)),
        "duplicate_order_lines": (_duplicates(lines, "order_item_id"), len(lines)),
        "invalid_menu_prices": (_bad_price(menu["base_price"]).sum() + _bad_price(price).sum()
                                + _bad_price(pricing["unit_price"]).sum(),
                                len(menu) + len(lines) + len(pricing)),
        "negative_quantities": ((qty < 0).sum() + (num(inventory["consumption_quantity"]) < 0).sum(),
                                len(lines) + len(inventory)),
        "invalid_dates": (_bad_dates(orders["order_timestamp"]).sum()
                          + _bad_dates(ratings["rating_timestamp"]).sum()
                          + _bad_dates(wastage["wastage_date"]).sum(),
                          len(orders) + len(ratings) + len(wastage)),
        "invalid_ratings": ((ratings["rating_value"].notna()
                             & ~rating.isin([1, 2, 3, 4, 5])).sum(), len(ratings)),
        "missing_customer_ids": (orders["customer_id"].isna().sum(), len(orders)),
        "missing_menu_ids": (lines["menu_item_id"].isna().sum(), len(lines)),
        "invalid_restaurant_ids": (orphan_mask(orders["restaurant_id"], rest_ids).sum(), len(orders)),
        "impossible_wastage": (_impossible_wastage(wastage, inventory), len(wastage)),
        "incorrect_discounts": (bad_line_discount.sum() + bad_order_discount.sum(),
                                len(lines) + len(orders)),
        "cancelled_transactions": (orders["order_status"].astype(str).str.strip().str.lower()
                                   .eq("cancelled").sum(), len(orders)),
        "inconsistent_units": (_unit_mismatch(inventory, unit_by_item).sum()
                               + _unit_mismatch(wastage, unit_by_item).sum(),
                               len(inventory) + len(wastage)),
        "invalid_location_references": (location_orphans,
                                        len(orders) + len(ratings) + len(inventory) + len(wastage)),
    }
    return {k: {"count": int(c), "rows_checked": int(n)} for k, (c, n) in counts.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(REPO_ROOT / "reports" / "evidence"
                                             / "independent_quality_counts.json"))
    args = parser.parse_args()
    cache = {}

    def load(table):
        if table not in cache:
            cache[table] = read_table(RAW_DIR, table)
        return cache[table]

    found = detect(load)
    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_dir": str(DATA_DIR),
        "method": "pandas (independent of Spark)",
        "defects": {k: {**v, "definition": DEFINITIONS[k]} for k, v in found.items()},
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for name, d in found.items():
        print(f"{name:30s} {d['count']:>10,} / {d['rows_checked']:,}")
    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()

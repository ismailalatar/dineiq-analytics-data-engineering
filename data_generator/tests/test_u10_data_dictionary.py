"""U10 self-tests — verify data dictionary matches generated CSVs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path("D:/APTECH")
DICT_PATH = ROOT / "documentation" / "data_dictionary" / "data_dictionary.json"
RAW_DIR = ROOT / "full_output" / "raw_data"


def run_u10_tests() -> bool:
    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("Dictionary file exists", DICT_PATH.exists(), str(DICT_PATH))
    if not DICT_PATH.exists():
        _print(results)
        return False

    with DICT_PATH.open("r", encoding="utf-8") as f:
        dd = json.load(f)

    check("Dictionary has 'tables' section", "tables" in dd)
    tables = dd.get("tables", {})

    expected_tables = {
        "Customers", "Restaurants", "Menu_Categories", "Menu_Items",
        "Pricing_History", "Promotions", "Promotion_Items",
        "Orders", "Order_Items", "Ratings", "Inventory", "Wastage",
    }
    check("Dictionary covers all 12 expected tables",
          set(tables.keys()) == expected_tables,
          f"missing={expected_tables - set(tables.keys())}, extra={set(tables.keys()) - expected_tables}")

    check("Raw data folder exists", RAW_DIR.exists(), str(RAW_DIR))
    if not RAW_DIR.exists():
        _print(results)
        return False

    for table_name, spec in tables.items():
        csv_path = RAW_DIR / f"{table_name}.csv"
        check(f"CSV exists: {table_name}", csv_path.exists())

        if not csv_path.exists():
            continue

        df_header = pd.read_csv(csv_path, nrows=0)
        actual_cols = list(df_header.columns)
        expected_cols = [c["name"] for c in spec.get("columns", [])]

        check(f"Column set matches: {table_name}",
              actual_cols == expected_cols,
              f"csv={actual_cols}, dict={expected_cols}")

        pk = spec.get("primary_key", [])
        for col in pk:
            check(f"PK column '{col}' present in {table_name}",
                  col in actual_cols)

        fks = spec.get("foreign_keys", [])
        for fk in fks:
            check(f"FK column '{fk['column']}' present in {table_name}",
                  fk["column"] in actual_cols)

    # Required key checks
    required_pks = {
        "Customers": "customer_id",
        "Restaurants": "restaurant_id",
        "Menu_Categories": "category_id",
        "Menu_Items": "menu_item_id",
        "Pricing_History": "pricing_history_id",
        "Promotions": "promotion_id",
        "Orders": "order_id",
        "Order_Items": "order_item_id",
        "Ratings": "rating_id",
        "Inventory": "inventory_id",
        "Wastage": "wastage_id",
    }
    for tbl, pk in required_pks.items():
        spec = tables.get(tbl, {})
        check(f"Primary key of {tbl} == ['{pk}']",
              spec.get("primary_key") == [pk],
              f"got {spec.get('primary_key')}")

    # Promotion_Items composite PK
    check("Promotion_Items has composite PK",
          set(tables.get("Promotion_Items", {}).get("primary_key", [])) ==
          {"promotion_id", "menu_item_id"})

    # Orders foreign keys
    orders_fks = {fk["column"] for fk in tables.get("Orders", {}).get("foreign_keys", [])}
    check("Orders has FK to Customers/Restaurants/Promotions",
          orders_fks == {"customer_id", "restaurant_id", "promotion_id"},
          str(orders_fks))

    # Ratings foreign keys
    ratings_fks = {fk["column"] for fk in tables.get("Ratings", {}).get("foreign_keys", [])}
    check("Ratings has FK to Customers/Menu_Items/Restaurants",
          ratings_fks == {"customer_id", "menu_item_id", "restaurant_id"},
          str(ratings_fks))

    # Channel values documented
    orders_channels = None
    for col in tables.get("Orders", {}).get("columns", []):
        if col["name"] == "order_channel":
            orders_channels = col.get("allowed_values")
            break
    expected_channels = {
        "Dine-in", "Takeaway", "Restaurant Website/App",
        "Third-party delivery platforms", "Other supported channels",
    }
    if orders_channels:
        doc_set = set(v.strip() for v in orders_channels.split(","))
        check("Channel values in dictionary match SRS",
              expected_channels.issubset(doc_set),
              f"doc={doc_set}")

    _print(results)
    return all(r[1] for r in results)


def _print(results):
    print("\n" + "=" * 72)
    print("U10 SELF-TESTS")
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


if __name__ == "__main__":
    ok = run_u10_tests()
    raise SystemExit(0 if ok else 1)
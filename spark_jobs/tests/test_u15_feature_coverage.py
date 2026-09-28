"""U15 — Feature Coverage Functional Test (v3)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path


ROOT = Path("D:/APTECH")
FEAT = ROOT / "full_output" / "processed_data" / "features"


# (feature_name, table, column, type_kind, (min,max), max_nan_pct, description)
FEATURES = [
    ("Item revenue",              "item_features", "revenue",                "numeric", (0, None),    0.00, "SUM(line_total) per item"),
    ("Cost",                      "item_features", "cost",                   "numeric", (0, None),    0.00, "SUM(qty*unit_cost)"),
    ("Contribution margin",       "item_features", "contribution_margin",    "numeric", (None, None), 0.00, "revenue - cost"),
    ("Profit percentage",         "item_features", "profit_pct",             "numeric", (-1.0, 1.0),  0.00, "margin / revenue"),
    ("Order frequency",           "item_features", "order_frequency",        "numeric", (0, None),    0.00, "COUNT(DISTINCT order_id)"),
    ("Item popularity",           "item_features", "quantity_sold",          "numeric", (0, None),    0.00, "SUM(quantity)"),
    ("Repeat-purchase rate",      "item_features", "repeat_purchase_rate",   "numeric", (0.0, 1.0),   0.00, "repeat_customers / customers"),
    ("Average rating",            "item_features", "avg_rating",             "numeric", (1.0, 5.0),   0.20, "AVG(rating_value)"),
    ("Rating trend",              "item_features", "rating_trend",           "numeric", (-4.0, 4.0),  0.20, "recent_avg - early_avg"),
    ("Wastage percentage",        "item_features", "wastage_pct",            "numeric", (0.0, None),  0.00, "wasted / consumption"),
    ("Promotion dependency",      "item_features", "promotion_dependency",   "numeric", (0.0, 1.0),   0.00, "qty_promoted / qty_sold"),
    ("Discount percentage",       "item_features", "discount_pct",           "numeric", (0.0, 1.0),   0.00, "discount / (revenue+discount)"),
    ("Price-change percentage",   "item_features", "price_change_pct",       "numeric", (-1.0, None), 0.00, "(max-min)/min"),
    ("Customer recency",          "customer_features", "recency_days",       "numeric", (0, None),    0.00, "datediff(last_activity, ref)"),
    ("Customer frequency",        "customer_features", "order_count",        "numeric", (0, None),    0.00, "COUNT(DISTINCT order_id)"),
    ("Customer monetary value",   "customer_features", "monetary",           "numeric", (0, None),    0.00, "SUM(line_total)"),
    ("Average order value",       "customer_features", "average_order_value","numeric", (0, None),    0.00, "monetary / order_count"),
    ("Weekend-order ratio",       "customer_features", "weekend_ratio",      "numeric", (0.0, 1.0),   0.00, "weekend_orders / order_count"),
    ("Channel preference",        "customer_features", "preferred_channel",  "string",  None,         0.25, "modal order_channel (may be null for non-buyers)"),
    ("Peak-hour frequency",       "order_features", "is_peak_hour",          "binary",  (0, 1),       0.00, "1 if hour in 11..21"),
    ("Basket size",               "order_features", "basket_size",           "numeric", (1, None),    0.00, "COUNT(order_items) per order"),
    ("Location performance",      "location_item_features", "revenue",       "numeric", (0, None),    0.00, "SUM(line_total) per (loc, item)"),
]


def _is_numeric(s): return pd.api.types.is_numeric_dtype(s)
def _is_string(s):  return pd.api.types.is_string_dtype(s) or s.dtype == object
def _is_binary(s):
    try: return set(s.dropna().unique()).issubset({0, 1})
    except Exception: return False


def run_u15_tests() -> bool:
    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    needed = {f[1] for f in FEATURES}
    tables = {}
    for tbl in needed:
        path = FEAT / f"{tbl}.parquet"
        if not path.exists():
            check(f"Table exists: {tbl}", False, str(path))
            continue
        tables[tbl] = pd.read_parquet(path)
        check(f"Table exists: {tbl}", True, f"{len(tables[tbl])} rows")

    for feature, table, col, ttype, rng, max_nan, desc in FEATURES:
        if table not in tables:
            check(f"{feature}: table missing", False); continue
        df = tables[table]
        if col not in df.columns:
            check(f"{feature}: column '{col}' missing", False); continue

        series = df[col]

        if ttype == "numeric":
            check(f"{feature}: dtype numeric", _is_numeric(series), str(series.dtype))
        elif ttype == "string":
            check(f"{feature}: dtype string", _is_string(series), str(series.dtype))
        elif ttype == "binary":
            check(f"{feature}: dtype binary {0,1}", _is_binary(series),
                  f"unique={sorted(series.dropna().unique())[:5]}")

        nan_count = int(series.isna().sum())
        nan_ratio = nan_count / max(1, len(series))
        check(f"{feature}: NaN ratio <= {max_nan:.0%}",
              nan_ratio <= max_nan,
              f"{nan_count}/{len(series)} = {nan_ratio:.2%}")

        if rng is not None and _is_numeric(series):
            s = series.replace([np.inf, -np.inf], np.nan).dropna()
            if len(s) > 0:
                lo, hi = rng
                ok_lo = True if lo is None else bool((s >= lo).all())
                ok_hi = True if hi is None else bool((s <= hi).all())
                check(f"{feature}: range within {rng}",
                      ok_lo and ok_hi,
                      f"min={s.min()}, max={s.max()}")

    print("\n" + "=" * 72)
    print("U15 FEATURE COVERAGE TESTS")
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
    return fails == 0


if __name__ == "__main__":
    ok = run_u15_tests()
    raise SystemExit(0 if ok else 1)
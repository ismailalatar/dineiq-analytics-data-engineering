"""
نتحقق من بيانات الطالب الاول
نطلع تقارير parquet في results/parquet
"""

import pandas as pd

from python_pipeline.config import (
    REQUIRED_TABLES,
    MIN_ROWS,
    PARQUET_DIR,
    FEATURE_WINDOW_END,
    LABEL_WINDOW_START,
)
from python_pipeline.lib.io_helpers import load_clean_table, save_parquet
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


# الاعمده الي ما يصير فيها NULL
CRITICAL_COLS = {
    "Customers": ["customer_id"],
    "Orders": ["order_id", "customer_id"],
    "Order_Items": ["order_item_id", "order_id"],
    "Menu_Items": ["menu_item_id", "category_id"],
    "Menu_Categories": ["category_id"],
    "Restaurants": ["restaurant_id"],
    "Ratings": ["rating_id", "rating_value"],
    "Wastage": ["wastage_id"],
}


def check_rows(data):
    out = []
    for tbl, min_n in MIN_ROWS.items():
        df = data.get(tbl)
        if df is None:
            out.append({"table": tbl, "check": "rows", "status": "FAIL",
                        "reason": "table missing"})
            continue
        actual = len(df)
        status = "PASS" if actual >= min_n else "WARN"
        out.append({
            "table": tbl,
            "check": "rows",
            "actual": int(actual),
            "min": int(min_n),
            "status": status,
        })
    return pd.DataFrame(out)


def check_columns(data):
    out = []
    for tbl, cols in CRITICAL_COLS.items():
        df = data.get(tbl)
        if df is None:
            continue
        missing = [c for c in cols if c not in df.columns]
        status = "PASS" if not missing else "FAIL"
        out.append({
            "table": tbl,
            "check": "columns",
            "missing": ", ".join(missing) if missing else "",
            "status": status,
        })
    return pd.DataFrame(out)


def check_nulls(data):
    out = []
    for tbl, cols in CRITICAL_COLS.items():
        df = data.get(tbl)
        if df is None:
            continue
        for c in cols:
            if c not in df.columns:
                continue
            n_null = int(df[c].isna().sum())
            status = "PASS" if n_null == 0 else "WARN"
            out.append({
                "table": tbl,
                "check": f"nulls_in_{c}",
                "nulls": n_null,
                "status": status,
            })
    return pd.DataFrame(out)


def check_date_range(data):
    orders = data.get("Orders")
    if orders is None:
        return pd.DataFrame()

    ts = pd.to_datetime(orders["order_timestamp"], errors="coerce")
    return pd.DataFrame([{
        "check": "date_range",
        "min_date": str(ts.min()),
        "max_date": str(ts.max()),
        "feature_cutoff": FEATURE_WINDOW_END,
        "label_start": LABEL_WINDOW_START,
        "status": "PASS",
    }])


def run():
    log.info("نبدا التحقق")
    data = {}
    for tbl in REQUIRED_TABLES:
        data[tbl] = load_clean_table(tbl)

    # نحفظ كل فحص بجدول مستقل
    save_parquet(check_rows(data),     PARQUET_DIR / "validation_rows.parquet")
    save_parquet(check_columns(data),  PARQUET_DIR / "validation_columns.parquet")
    save_parquet(check_nulls(data),    PARQUET_DIR / "validation_nulls.parquet")
    save_parquet(check_date_range(data), PARQUET_DIR / "validation_dates.parquet")

    # ملخص شامل
    all_checks = pd.concat(
        [
            check_rows(data),
            check_columns(data),
            check_nulls(data),
        ],
        ignore_index=True,
    )

    summary = pd.DataFrame([{
        "total": int(len(all_checks)),
        "pass": int((all_checks["status"] == "PASS").sum()),
        "warn": int((all_checks["status"] == "WARN").sum()),
        "fail": int((all_checks["status"] == "FAIL").sum()),
    }])
    save_parquet(summary, PARQUET_DIR / "validation_summary.parquet")

    log.info(f"الملخص: {summary.to_dict(orient='records')[0]}")
    return summary


if __name__ == "__main__":
    run()
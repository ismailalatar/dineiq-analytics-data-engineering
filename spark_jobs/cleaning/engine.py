from __future__ import annotations

import json
import time
from pathlib import Path

from pyspark.sql import SparkSession

from ..ingestion.schemas import SCHEMAS
from . import rules as CR


ROOT = Path("D:/APTECH")
RAW = ROOT / "full_output" / "raw_data"
CLEAN = ROOT / "full_output" / "processed_data" / "clean"
QUAR = ROOT / "full_output" / "processed_data" / "quarantine"
REPORTS = ROOT / "full_output" / "reports"


def _load(spark, name):
    return (
        spark.read
        .option("header", "true")
        .option("mode", "PERMISSIVE")
        .option("nullValue", "")
        .schema(SCHEMAS[name])
        .csv(str(RAW / f"{name}.csv"))
    )


def _count_df(df):
    """Count rows safely. Returns int or None."""
    if df is None:
        return None
    try:
        return int(df.count())
    except Exception:
        return None


def run_cleaning():
    start = time.time()
    CLEAN.mkdir(parents=True, exist_ok=True)
    QUAR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("DineIQ-U13-Cleaning")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print("[load] Reading raw tables via Spark ...")
    T = {n: _load(spark, n) for n in SCHEMAS.keys()}

    log = []

    def log_step(name, clean, quar, desc):
        """Record a cleaning step. clean/quar can be a DataFrame or a tuple of them."""
        clean_rows = None
        quar_rows = None
        if isinstance(clean, tuple):
            parts = [_count_df(x) for x in clean]
            if any(p is not None for p in parts):
                clean_rows = sum(p for p in parts if p is not None)
        else:
            clean_rows = _count_df(clean)
        if isinstance(quar, tuple):
            parts = [_count_df(x) for x in quar]
            if any(p is not None for p in parts):
                quar_rows = sum(p for p in parts if p is not None)
        else:
            quar_rows = _count_df(quar)

        entry = {
            "step": name,
            "description": desc,
            "clean_rows": clean_rows,
            "quarantine_rows": quar_rows,
        }
        log.append(entry)
        print(f"  [{name}] clean={clean_rows} quar={quar_rows}")

    def save_quar(df, name):
        if df is None:
            return
        try:
            df.write.mode("overwrite").parquet(str(QUAR / f"{name}.parquet"))
        except Exception as e:
            print(f"  [warn] could not save quarantine {name}: {e}")

    # ---- Step 1: missing values ----
    T["Orders"], quar, desc = CR.clean_missing_values(
        T["Orders"], T["Order_Items"], T["Menu_Items"], T["Pricing_History"]
    )
    log_step("missing_values", T["Orders"], quar, desc)
    save_quar(quar, "orders_missing_values")

    # ---- Step 2: duplicate orders ----
    T["Orders"], quar, desc = CR.clean_duplicate_orders(T["Orders"])
    log_step("dup_orders", T["Orders"], quar, desc)
    save_quar(quar, "orders_duplicates")

    # ---- Step 3: duplicate lines ----
    T["Order_Items"], quar, desc = CR.clean_duplicate_order_items(T["Order_Items"])
    log_step("dup_lines", T["Order_Items"], quar, desc)
    save_quar(quar, "order_items_duplicates")

    # ---- Step 4: invalid menu prices ----
    T["Menu_Items"], quar, desc = CR.clean_invalid_menu_prices(T["Menu_Items"])
    log_step("menu_prices", T["Menu_Items"], quar, desc)
    save_quar(quar, "menu_invalid_prices")

    # ---- Step 5: negative quantities ----
    T["Order_Items"], quar, desc = CR.clean_negative_quantities(T["Order_Items"])
    log_step("neg_quantities", T["Order_Items"], quar, desc)
    save_quar(quar, "order_items_negative")

    T["Inventory"], quar, desc = CR.clean_negative_inventory_consumption(T["Inventory"])
    log_step("neg_inventory", T["Inventory"], quar, desc)
    save_quar(quar, "inventory_negative")

    # ---- Step 6: invalid dates ----
    (T["Orders"], T["Ratings"], T["Wastage"]), (qo, qr, qw), desc = CR.clean_invalid_dates(
        T["Orders"], T["Ratings"], T["Wastage"]
    )
    log_step("invalid_dates", (T["Orders"], T["Ratings"], T["Wastage"]), (qo, qr, qw), desc)
    save_quar(qo, "orders_bad_dates")
    save_quar(qr, "ratings_bad_dates")
    save_quar(qw, "wastage_bad_dates")

    # ---- Step 7: invalid ratings ----
    T["Ratings"], quar, desc = CR.clean_invalid_ratings(T["Ratings"])
    log_step("invalid_ratings", T["Ratings"], quar, desc)
    save_quar(quar, "ratings_invalid")

    # ---- Step 8: missing IDs ----
    (T["Orders"], T["Order_Items"]), (qo, ql), desc = CR.clean_missing_ids(
        T["Orders"], T["Order_Items"]
    )
    log_step("missing_ids", (T["Orders"], T["Order_Items"]), (qo, ql), desc)
    save_quar(qo, "orders_missing_customer")
    save_quar(ql, "lines_missing_item")

    # ---- Step 9: invalid restaurant refs ----
    T["Orders"], quar, desc = CR.clean_invalid_restaurant_ids(T["Orders"], T["Restaurants"])
    log_step("bad_restaurants", T["Orders"], quar, desc)
    save_quar(quar, "orders_bad_restaurant")

    # ---- Step 10: impossible wastage ----
    T["Wastage"], quar, desc = CR.clean_impossible_wastage(T["Wastage"], T["Inventory"])
    log_step("impossible_wastage", T["Wastage"], quar, desc)
    save_quar(quar, "wastage_impossible")

    # ---- Step 11: incorrect discounts ----
    T["Order_Items"], quar, desc = CR.clean_incorrect_discounts(T["Order_Items"])
    log_step("bad_discounts", T["Order_Items"], quar, desc)
    save_quar(quar, "order_items_discounts")

    # ---- Step 12: units ----
    (T["Inventory"], T["Wastage"]), (qi, qw), desc = CR.clean_inconsistent_units(
        T["Inventory"], T["Wastage"], T["Menu_Items"]
    )
    log_step("units", (T["Inventory"], T["Wastage"]), (qi, qw), desc)
    save_quar(qi, "inventory_bad_units")
    save_quar(qw, "wastage_bad_units")

    # ---- Step 13: cancelled transactions ----
    T["Orders"], _, desc = CR.clean_cancelled_transactions(T["Orders"])
    log_step("cancelled", T["Orders"], None, desc)

    # ---- Save cleaned ----
    print("[save] Writing cleaned tables to processed_data/clean/ ...")
    for name, df in T.items():
        df.write.mode("overwrite").parquet(str(CLEAN / f"{name}.parquet"))

    # ---- Report ----
    report = {
        "steps": log,
        "elapsed_seconds": round(time.time() - start, 2),
        "output_clean_dir": str(CLEAN),
        "output_quarantine_dir": str(QUAR),
    }
    with (REPORTS / "cleaning_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nDone in {report['elapsed_seconds']}s.")
    spark.stop()
    return report


if __name__ == "__main__":
    run_cleaning()
    
    





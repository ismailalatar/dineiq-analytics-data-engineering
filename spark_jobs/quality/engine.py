from __future__ import annotations

import json
import time
from pathlib import Path

from pyspark.sql import SparkSession

from ..ingestion.schemas import SCHEMAS
from . import rules as R


ROOT = Path("D:/APTECH")
RAW = ROOT / "full_output" / "raw_data"
REPORTS = ROOT / "full_output" / "reports"


def _load_tables(spark):
    tables = {}
    for name, schema in SCHEMAS.items():
        tables[name] = (
            spark.read
            .option("header", "true")
            .option("mode", "PERMISSIVE")
            .option("nullValue", "")
            .schema(schema)
            .csv(str(RAW / f"{name}.csv"))
        )
    return tables


def run_data_quality_check():
    start = time.time()
    REPORTS.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("DineIQ-U12-DataQuality")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print("[load] Reading all 12 tables via Spark ...")
    t = _load_tables(spark)

    print("[DQ] Running 15 data-quality rules ...")
    results = []

    results.append(R.check_missing_values(t["Orders"], t["Order_Items"], t["Menu_Items"], t["Pricing_History"]))
    results.append(R.check_duplicate_orders(t["Orders"]))
    results.append(R.check_duplicate_order_items(t["Order_Items"]))
    results.append(R.check_invalid_menu_prices(t["Menu_Items"]))
    results.append(R.check_negative_quantities(t["Order_Items"], t["Inventory"]))
    results.append(R.check_invalid_dates(t["Orders"], t["Ratings"], t["Wastage"]))
    results.append(R.check_invalid_ratings(t["Ratings"]))
    results.append(R.check_missing_customer_ids(t["Orders"]))
    results.append(R.check_missing_menu_ids(t["Order_Items"]))
    results.append(R.check_invalid_restaurant_ids(t["Orders"], t["Restaurants"]))
    results.append(R.check_impossible_wastage(t["Wastage"], t["Inventory"]))
    results.append(R.check_incorrect_discounts(t["Order_Items"]))
    results.append(R.check_cancelled_transactions(t["Orders"]))
    results.append(R.check_inconsistent_units(t["Inventory"], t["Wastage"], t["Menu_Items"]))
    results.append(R.check_invalid_location_references(
        t["Orders"], t["Inventory"], t["Wastage"], t["Restaurants"]
    ))

    for r in results:
        print(f"  {r['rule']:<40} {r['total']}")

    passed = sum(1 for r in results if r["total"] > 0)
    failed = len(results) - passed

    report = {
        "checks": results,
        "total_rules": len(results),
        "rules_with_findings": passed,
        "rules_with_no_findings": failed,
        "elapsed_seconds": round(time.time() - start, 2),
    }

    out_path = REPORTS / "data_quality_report.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'=' * 72}")
    print("DATA QUALITY SUMMARY")
    print(f"{'=' * 72}")
    print(f"Rules with findings:    {passed}/{len(results)}")
    print(f"Rules with no findings: {failed}/{len(results)}")
    print(f"Report: {out_path}")
    print(f"Elapsed: {report['elapsed_seconds']}s")
    print(f"{'=' * 72}")

    spark.stop()
    return report


if __name__ == "__main__":
    run_data_quality_check()

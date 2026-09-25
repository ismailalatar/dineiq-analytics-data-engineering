from __future__ import annotations

import json
from pathlib import Path

from spark_jobs.ingestion.ingest import run_ingestion


ROOT = Path("D:/APTECH")
REPORT = ROOT / "full_output" / "reports" / "step3_ingestion_report.json"


def run_u11_tests() -> bool:
    run_ingestion()

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("Ingestion report written", REPORT.exists(), str(REPORT))
    if not REPORT.exists():
        _print(results)
        return False

    with REPORT.open("r", encoding="utf-8") as f:
        report = json.load(f)

    expected = {
        "Customers", "Restaurants", "Menu_Categories", "Menu_Items",
        "Pricing_History", "Promotions", "Promotion_Items",
        "Orders", "Order_Items", "Ratings", "Inventory", "Wastage",
    }
    check("All 12 tables ingested",
          set(report["tables"].keys()) == expected,
          f"missing={expected - set(report['tables'].keys())}")

    expected_rows = {
        "Customers": 50_000,
        "Menu_Items": 150,
        "Menu_Categories": 10,
        "Restaurants": 20,
        "Ratings": 100_000,
        "Wastage": 50_000,
    }
    for tbl, min_rows in expected_rows.items():
        rows = report["tables"].get(tbl, {}).get("rows", 0)
        check(f"{tbl} rows >= {min_rows:,}", rows >= min_rows, f"{rows:,}")

    oi_rows = report["tables"].get("Order_Items", {}).get("rows", 0)
    check("Order_Items rows >= 1,000,000", oi_rows >= 1_000_000, f"{oi_rows:,}")

    o_rows = report["tables"].get("Orders", {}).get("rows", 0)
    check("Orders rows >= 100,000", o_rows >= 100_000, f"{o_rows:,}")

    check("Schema inference present",
          "Order_Items" == report.get("schema_inference", {}).get("table"),
          str(report.get("schema_inference", {}).get("table")))

    tv = report.get("type_validation", {})
    check("Type validation passed", tv.get("passed") is True,
          f"mismatches={len(tv.get('mismatches', []))}")

    lf = report.get("large_file_loading", {})
    check("Large file loaded", lf.get("loaded_successfully") is True)

    ph = report.get("partition_handling", {})
    check("Partitioned by order_id",
          ph.get("partitioned_by") == "order_id", str(ph.get("partitioned_by")))
    check("Partition count > 1",
          ph.get("partitions_after", 0) > 1, str(ph.get("partitions_after")))

    rb = report.get("readback_validation", {})
    check("Readback matches ingest", rb.get("matches_ingest") is True)

    _print(results)
    return all(r[1] for r in results)


def _print(results):
    print("\n" + "=" * 72)
    print("U11 SELF-TESTS")
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
    ok = run_u11_tests()
    raise SystemExit(0 if ok else 1)
from __future__ import annotations

import json
from pathlib import Path

from spark_jobs.features.engineering import run_feature_engineering


ROOT = Path("D:/APTECH")
REPORT = ROOT / "full_output" / "reports" / "feature_engineering_report.json"
FEAT = ROOT / "full_output" / "processed_data" / "features"


def run_u14_tests() -> bool:
    run_feature_engineering()

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("Feature report written", REPORT.exists(), str(REPORT))
    check("Features folder exists", FEAT.exists(), str(FEAT))

    if not REPORT.exists():
        _print(results)
        return False

    with REPORT.open("r", encoding="utf-8") as f:
        report = json.load(f)

    check("Fact table has rows >= 1,000,000",
          report.get("fact_rows", 0) >= 1_000_000,
          f"{report.get('fact_rows'):,}")

    check("Item features rows == 150",
          report.get("item_features_rows", 0) == 150,
          f"{report.get('item_features_rows')}")

    check("Customer features rows == 50,000",
          report.get("customer_features_rows", 0) == 50_000,
          f"{report.get('customer_features_rows'):,}")

    check("Order features rows >= 90,000 (post-cleaning)",
          report.get("order_features_rows", 0) >= 90_000,
          f"{report.get('order_features_rows'):,}")

    check("Location × Item features rows > 0",
          report.get("location_item_features_rows", 0) > 0,
          f"{report.get('location_item_features_rows'):,}")

    check("Time features rows > 0",
          report.get("time_features_rows", 0) > 0,
          f"{report.get('time_features_rows')}")

    check("SRS Step 6: 10 joins implemented",
          report.get("srs_step_6_joins") == 10)
    check("SRS Step 7: 22 features produced",
          report.get("srs_step_7_features_produced") == 22)

    for f in ["item_features", "customer_features", "order_features",
              "location_item_features", "time_features"]:
        check(f"Parquet exists: {f}", (FEAT / f"{f}.parquet").exists())

    _print(results)
    return all(r[1] for r in results)


def _print(results):
    print("\n" + "=" * 72)
    print("U14 SELF-TESTS")
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
    ok = run_u14_tests()
    raise SystemExit(0 if ok else 1)

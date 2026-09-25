from __future__ import annotations

import json
from pathlib import Path

from spark_jobs.cleaning.engine import run_cleaning


ROOT = Path("D:/APTECH")
REPORT = ROOT / "full_output" / "reports" / "cleaning_report.json"
CLEAN = ROOT / "full_output" / "processed_data" / "clean"
QUAR = ROOT / "full_output" / "processed_data" / "quarantine"


def run_u13_tests() -> bool:
    run_cleaning()

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("Cleaning report written", REPORT.exists(), str(REPORT))
    check("Clean folder exists", CLEAN.exists(), str(CLEAN))
    check("Quarantine folder exists", QUAR.exists(), str(QUAR))

    if not REPORT.exists():
        _print(results)
        return False

    with REPORT.open("r", encoding="utf-8") as f:
        report = json.load(f)

    steps = report.get("steps", [])
    check("Cleaning has at least 10 steps", len(steps) >= 10, f"{len(steps)}")

    # Every step must record a description
    for s in steps:
        check(f"Step '{s['step']}' has description",
              isinstance(s.get("description"), str) and len(s["description"]) > 5,
              s.get("description", "")[:50])

    # Verify output tables exist
    for table in [
        "Customers", "Restaurants", "Menu_Categories", "Menu_Items",
        "Pricing_History", "Promotions", "Promotion_Items",
        "Orders", "Order_Items", "Ratings", "Inventory", "Wastage",
    ]:
        p = CLEAN / f"{table}.parquet"
        check(f"Clean Parquet exists: {table}", p.exists())

    _print(results)
    return all(r[1] for r in results)


def _print(results):
    print("\n" + "=" * 72)
    print("U13 SELF-TESTS")
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
    ok = run_u13_tests()
    raise SystemExit(0 if ok else 1)
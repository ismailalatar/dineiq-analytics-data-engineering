from __future__ import annotations

import json
from pathlib import Path

from spark_jobs.quality.engine import run_data_quality_check


REPORT = Path("D:/APTECH/full_output/reports/data_quality_report.json")


def run_u12_tests() -> bool:
    run_data_quality_check()

    results = []
    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("Report file written", REPORT.exists(), str(REPORT))
    if not REPORT.exists():
        _print(results)
        return False

    with REPORT.open("r", encoding="utf-8") as f:
        report = json.load(f)

    checks = report.get("checks", [])
    check("All 15 rules ran", len(checks) == 15, f"{len(checks)}")

    for c in checks:
        n = c.get("total", 0)
        check(f"{c['rule']} found anomalies", n > 0, f"{n}")

    _print(results)
    return all(r[1] for r in results)


def _print(results):
    print("\n" + "=" * 72)
    print("U12 SELF-TESTS")
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
    ok = run_u12_tests()
    raise SystemExit(0 if ok else 1)
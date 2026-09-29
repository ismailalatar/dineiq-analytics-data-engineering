"""Run the test suite and write submission evidence.

Usage (from the repo root; extra arguments are passed to pytest):
    python tests/tools/run_tests_with_report.py [-k schema]
Outputs:
    reports/test_results/junit.xml
    reports/test_results/TEST_RESULTS.md
"""
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.data_access import DATA_DIR  # noqa: E402

OUT = ROOT / "reports" / "test_results"


def _first_line(text):
    lines = (text or "").strip().splitlines()
    return lines[0][:140].replace("|", "\\|") if lines else ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    xml_path = OUT / "junit.xml"
    started = datetime.now()
    code = subprocess.run([sys.executable, "-m", "pytest", f"--junitxml={xml_path}",
                           *sys.argv[1:]], cwd=ROOT).returncode
    if not xml_path.exists():
        sys.exit(f"pytest produced no report (exit code {code})")

    totals = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    rows = []
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        status, note = "passed", ""
        for tag in ("failure", "error", "skipped"):
            el = case.find(tag)
            if el is not None:
                status = "failed" if tag == "failure" else tag
                note = _first_line(el.get("message") or el.text)
                break
        totals[status] += 1
        module = (case.get("classname") or "").split(".")[-1]
        rows.append(f"| {module} | {case.get('name')} | {status} | {case.get('time', '')} | {note} |")

    md = [
        "# Automated Test Results", "",
        f"- Run at: {started:%Y-%m-%d %H:%M}",
        f"- Python: {platform.python_version()} on {platform.system()} {platform.release()}",
        f"- Data directory: `{DATA_DIR}`",
        f"- pytest exit code: {code}", "",
        "| Passed | Failed | Errors | Skipped |", "|---|---|---|---|",
        f"| {totals['passed']} | {totals['failed']} | {totals['error']} | {totals['skipped']} |", "",
        "| Module | Test | Status | Time (s) | Note |", "|---|---|---|---|---|", *rows, "",
    ]
    (OUT / "TEST_RESULTS.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nEvidence written to {OUT}")
    sys.exit(code)


if __name__ == "__main__":
    main()

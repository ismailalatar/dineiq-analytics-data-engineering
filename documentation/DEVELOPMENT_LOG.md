# Development Log

Required by SRS v1.0 §1.8 item 3. Add one entry per member per day. Keep entries short and factual, and link commits where possible.

## Entry template

```
### Day N — YYYY-MM-DD — Student X (name)
- Work completed:
- Dataset changes:
- Data-quality problems found:
- Spark failures (error + fix):
- Model failures (error + fix):
- Changes made (commits):
- Tests performed (command + result):
- Performance improvements (before → after):
```

## Entries

### 2026-09-29 — Student 6 (Amal Rashad)
- Work completed: reviewed the repository and the generator code against SRS §1.10. Added:
  - README, INSTALLATION, PROJECT_REPORT skeleton, TEST_PLAN, EVIDENCE_INDEX;
  - SUBMISSION_CHECKLIST, DEVELOPMENT_LOG, TEAM_CONTRIBUTIONS, AI_USAGE, LICENSE;
  - the tests/ data-contract suite, merged with the team's existing tests/conftest.py via tests/data_fixtures.py;
  - independent quality counts (reports/evidence/) and raw sample data (sample_data/raw/).
- Dataset changes: none (regenerated locally with seed 42 for testing only; not committed).
- Data-quality problems found:
  - see SUBMISSION_CHECKLIST §A (clean-layer volume risk, launch_date missing from the dictionary, impossible-wastage count mismatch);
  - requirements.txt was missing the Flask packages, python-dotenv and the Excel export package, so the app tests could not run; reported to Student 4.
- Spark failures: n/a.
- Model failures: n/a.
- Changes made: see commits by amalrashad7804-source on 2026-09-29.
- Tests performed: `python tests/tools/run_tests_with_report.py` on Python 3.14 (GitHub Codespaces) → 146 passed, 0 failed, 18 skipped (clean-layer tests wait for Spark cleaning).
- Performance improvements: n/a.

# Final Submission Checklist

Owner: Student 6 · Source: SRS v1.0 §1.10 · Last review: 2026-09-29

Legend: ✅ done · ⏳ in progress · ⬜ not started · ⚠ risk

## A. Issues found in the repository review (2026-09-29)

| # | Issue | Why it matters | Action / owner |
|---|---|---|---|
| 1 | ⚠ Only 2 commits in the repository | SRS §1.8 item 2 requires meaningful commits across all five days, and §1.10 item 12 requires commits from **every** member | Every student pushes their own work, from their own account, in several small commits |
| 2 | ⚠ `.gitignore` lists `spark_analytics/` and `python_analytics/`, but neither folder is in the repo | Teammates' work may exist only on a laptop | Owners push these folders (ignoring only their large outputs) |
| 3 | ⚠ `.gitignore` excludes `*.log` and `full_output/` | Spark logs and reports never reach GitHub | Copy evidence into `reports/` and save logs as `.txt` (see EVIDENCE_INDEX) |
| 4 | ⚠ The clean layer may fall below 1,000,000 order lines | Dropping duplicates (~10.5k), negative/invalid lines and the lines of 5% cancelled orders could remove ~60k of 1,066,785 | S1: keep cancelled orders with a status flag, or raise generator volume. `test_08` checks this |
| 5 | `Menu_Items.launch_date` exists in the data but not in the data dictionary | The dictionary no longer matches the data | S1: add it to `DATA_DICTIONARY.md` and `.json` |
| 6 | The handoff reports 74 impossible-wastage rows, but `wastage.py` forces 2% (~1,000) | Evaluators may ask which number is right | S1 + S6: compare with `python -m tests.quality_checks` and document the definition used |
| 7 | `documentation/reports/DATA_ENGINEERING_REPORT.md` is referenced in the handoff but missing (404) | Broken evidence link | S1: push the file |
| 8 | Spark dependencies are not pinned | Installation cannot be reproduced | S1: add `requirements-spark.txt` |
| 9 | The handoff says "364 days" and the old README said "365 days" | The generator config covers 2024-01-01 to 2024-12-31, which is 366 calendar days (leap year) | Quote the date range, not a day count |
| 10 | The handoff document is in Arabic only | Evaluators may need English | Covered by `PROJECT_REPORT.md` |
| 11 | The README structure section was empty | Deliverable 2 | ✅ fixed |

## B. Deliverables

| # | Deliverable | Location | Owner | Status |
|---|---|---|---|---|
| 1 | Project report | `documentation/PROJECT_REPORT.md` | S6 (all contribute) | ⏳ skeleton |
| 2 | README.md | root | S6 | ✅ |
| 2 | AI_USAGE.md | root | all | ⏳ each member adds rows |
| 2 | requirements.txt | root | S4, S1 | ⏳ Spark deps missing |
| 2 | LICENSE | root | S6 | ✅ |
| 2 | Source folders (src, templates, static, spark_sql, python_pipeline, models, database, config, notebooks) | root | S1–S4 | ⬜ |
| 3 | Dataset scripts, dictionary, schemas, PK/FK | `data_generator/`, `documentation/data_dictionary/` | S1 | ✅ (dictionary needs `launch_date`) |
| 3 | Dataset statistics | `reports/dataset/` | S1 | ⏳ copy into repo |
| 3 | Raw and cleaned samples | `sample_data/` | S6 | ⬜ |
| 3 | Parquet datasets | Google Drive | S1 | ✅ confirm sharing is set to "Anyone with the link" |
| 3 | Train / validation / test sets | `processed_data/splits/` | S2 | ⬜ |
| 3 | Hidden-data readiness documentation | `documentation/testing/TEST_PLAN.md` §7 | S6 | ✅ |
| 4 | Spark processing evidence | `reports/spark/` | S1 | ⏳ |
| 5 | Spark MLlib evidence (at least 3 models compared) | `reports/mllib/`, `models/spark/` | S2 | ⬜ |
| 6 | Python model evidence | `reports/python/`, `models/python/` | S2 | ⬜ |
| 7 | Dual-pipeline comparison (at least 100 unseen records) | `reports/comparison/` | S2 | ⬜ |
| 8 | Restaurant Intelligence report | `reports/intelligence/` | S2/S3 | ⬜ |
| 9 | Test cases and results | `tests/`, `reports/test_results/` | S6 + owners | ⏳ |
| 10 | Installation instructions | `documentation/INSTALLATION.md` | S6 | ✅ draft |
| 11 | Execution instructions | README §5 | S6 | ⏳ fill as modules land |
| 12 | Screenshots | `screenshots/` | all | ⬜ |
| 12 | Evaluator credentials | README §8 | S4 | ⬜ |
| 13 | Deployed application URL | README quick links | S4 | ⬜ |
| 14 | Demonstration video (.mp4) | link in README | all (see §C) | ⬜ |
| 15 | Technical blog (at least 2,000 words) | link in README | S6 (proposed) | ⬜ |
| 16 | AI usage declaration | `AI_USAGE.md` | all | ⏳ |
| 17 | Project presentation | `documentation/presentation/` | all | ⬜ |
| 17 | Team contribution record | `documentation/TEAM_CONTRIBUTIONS.md` | S6 | ⏳ |
| – | Development log | `documentation/DEVELOPMENT_LOG.md` | all | ⏳ |

## C. Demonstration video shot list (SRS §1.10 item 14)

| # | Scene | Owner | Recorded |
|---|---|---|---|
| 1 | Login | S4 | ⬜ |
| 2 | Dataset generation | S1 | ⬜ |
| 3 | Spark ingestion | S1 | ⬜ |
| 4 | Spark processing + data-quality analysis | S1 | ⬜ |
| 5 | Data cleaning | S1 | ⬜ |
| 6 | Spark SQL queries | S1 | ⬜ |
| 7 | Feature engineering | S1 | ⬜ |
| 8 | Menu profitability + classification | S2 | ⬜ |
| 9 | Customer segmentation + RFM | S2 | ⬜ |
| 10 | Market-basket analysis | S2 | ⬜ |
| 11 | Peak-period analysis | S2 | ⬜ |
| 12 | Demand forecasting | S2 | ⬜ |
| 13 | Wastage analysis | S2 | ⬜ |
| 14 | Price intelligence | S2 | ⬜ |
| 15 | Promotion analysis | S2 | ⬜ |
| 16 | Anomaly detection | S2 | ⬜ |
| 17 | Spark prediction, then Python prediction | S2 | ⬜ |
| 18 | Dual-pipeline comparison | S2 | ⬜ |
| 19 | Recommendation engine with evidence | S3 | ⬜ |
| 20 | What-if scenario | S3 | ⬜ |
| 21 | Dashboards | S3 | ⬜ |
| 22 | Report generation / export | S4 | ⬜ |
| 23 | A difficult contradictory case (e.g. a loss-making bestseller) | S2 | ⬜ |
| 24 | Automated test run | S6 | ⬜ |

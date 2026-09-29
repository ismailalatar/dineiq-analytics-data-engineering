# Test Plan

Owner: Student 6 · Scope: SRS v1.0 §1.10 item 9 (Test Cases)

## 1. Objectives

1. Prove the dataset meets the SRS contract: volumes, schema, keys, relationships and business rules.
2. Prove the raw layer contains the defects and difficult cases the SRS requires, so later modules have something real to detect.
3. Give every module owner a place and a pattern for their own tests.
4. Produce evidence (JUnit XML and a Markdown report) for the submission.

The data tests were written against the generator code in `data_generator/` (`config.py`, `anomalies.py` and `generators/*.py`). Their thresholds are relative (quantiles and ratios), so they also work on a regenerated or hidden dataset.

## 2. Levels

| Level | What it checks | Where |
|---|---|---|
| Data-contract tests | Dataset volumes, schema, keys, rules, defects, difficult cases | `tests/test_01` … `test_08` |
| Unit tests | Individual functions of each module | `tests/test_<module>_*.py` (module owners) |
| Spark job tests | Ingestion, quality, cleaning, features | `spark_jobs/tests/` (Student 1) |
| Integration / end-to-end | API + database + UI flows | `tests/test_app_*.py` (Students 3/4) |
| Hidden-data readiness | Whole suite against an unseen dataset | §7 |

## 3. How to run

```bash
pytest                                           # everything
pytest tests/test_04_raw_defects.py -v           # one file
pytest -m clean_layer                            # clean-layer tests only
python tests/tools/run_tests_with_report.py      # with evidence report
```

When the dataset is absent (for example, on a fresh clone), the data tests are reported as **skipped**, not failed. The `-ra` option prints the reason.

## 4. Implemented test files

| File | SRS reference | What it asserts |
|---|---|---|
| `test_01_volume_and_history.py` | §1.2 Hint | Row minimums; 100k unique orders; 12 active months; multiple prices and promotions |
| `test_02_schema.py` | Step 3, FR xiii | Every documented column exists in CSV and Parquet; master keys are numeric and non-null |
| `test_03_keys_and_relationships.py` | Step 6, §1.2 Hint | Unique primary keys; all 10 SRS relationships plus `Promotion_Items` resolve (strict for master data, 1% tolerance for raw facts) |
| `test_04_raw_defects.py` | Step 4, §1.2 Hint | Each of the 15 defect types is present, but in fewer than 10% of the rows checked |
| `test_05_business_rules.py` | Data dictionary | `line_total` and `total_amount` formulas; allowed channels and statuses; rating targets; promotion dates |
| `test_06_difficult_cases.py` | Step 11, §1.10 item 9 | The difficult cases exist in the data: loss-making bestseller, low-selling high-margin dish, popular high-wastage dish, new item, location differences, weekend-only dish, promotion dependency, churn, rating spike, sales spike |
| `test_07_parquet_parity.py` | Step 2, FR xviii | Parquet row counts equal CSV row counts |
| `test_08_clean_layer.py` | Step 5, FR xv | After cleaning: unique IDs, no invalid values, FKs resolve 100%, no rows created, at least 1,000,000 lines remain |

`tests/quality_checks.py` counts the 15 defect types independently with pandas and writes each definition next to its count. Comparing this output with the Spark data-quality report is evidence that the Spark engine is correct. Where the two counts differ, the report must say whether the cause is a different definition or a bug.

## 5. SRS test categories: coverage and ownership

| # | SRS category | Status | Owner | A good test must check |
|---|---|---|---|---|
| 1 | Functional | ⬜ | S3/S4 | Each FR works through the UI or API |
| 2 | Integration | ◐ data-level | S6, S4 | Joins/FKs (done); API ↔ DB ↔ Spark outputs |
| 3 | Big Data ingestion | ◐ | S1, S6 | All tables load; explicit schema; multiple files; partitions |
| 4 | Schema validation | ✅ | S6 | Columns, types, keys |
| 5 | Data quality | ✅ raw / auto clean | S6 | 15 defects detected; clean layer free of them |
| 6 | Spark transformations | ⬜ | S1 | A small in-memory DataFrame goes in; exact rows come out |
| 7 | Spark SQL | ⬜ | S1 | Known input produces the exact expected aggregate |
| 8 | Spark models | ⬜ | S2 | 3 algorithms trained; saved model reloads; metrics recorded |
| 9 | Python models | ⬜ | S2 | Trained from raw/clean records, **not** from Spark outputs |
| 10 | Dual-pipeline comparison | ⬜ | S2 | At least 100 unseen records; agreement % computed; required columns present |
| 11 | Forecast | ⬜ | S2 | Train dates < test dates (Step 21); MAE/RMSE beat a naive baseline (NFR 4) |
| 12 | Basket analysis | ⬜ | S2 | 0 ≤ support, confidence ≤ 1; lift = confidence / support(consequent) |
| 13 | Wastage | ◐ data-level | S2 | Wastage % formula; risk labels reproducible |
| 14 | Promotion | ⬜ | S2 | The 8 generated trap promotions (40–55% discount) are flagged (Step 28) |
| 15 | Pricing | ◐ | S2 | Price-sensitive items (demand ∝ price^-2.5 in the generator) are classified Highly Price Sensitive |
| 16 | Anomaly | ◐ data-level | S2 | Injected anomalies are flagged by the detector |
| 17 | Security | ⬜ | S4 | Protected routes reject anonymous users; role limits; hashed passwords; rate limit |
| 18 | Boundary | ◐ | all | Ratings 1/5 edges; zero quantity; empty filters; single-row inputs |
| 19 | Hidden-data readiness | ◐ | S6 | §7 |

Legend: ✅ done · ◐ partial · ⬜ not started

## 6. Difficult cases: data vs module

`test_06` proves each case **exists in the data**. The module owner must add a test proving their module **handles** it.

| SRS difficult case | Data test (S6) | Module test (owner) |
|---|---|---|
| High-selling loss-making dish | ✅ | Classified as Volume Driver or Low Performer, never Profit Driver (S2) |
| Low-selling high-margin dish | ✅ | Classified as Hidden Opportunity (S2) |
| High-wastage popular dish | ✅ | Wastage recommendation generated (S3) |
| Promotion increasing sales but reducing profit | ⬜ | Trap promotion flagged (S2) |
| Dish performing differently across locations | ✅ | Different location-level classes (S2) |
| New menu item | ✅ | "Insufficient history" handling, using `launch_date`, with no forced class (S2) |
| Price-sensitive item | ⬜ | Classified Highly Price Sensitive (S2) |
| Customer churn | ✅ | Flagged as At-Risk (S2) |
| Rating anomaly | ✅ | Flagged by the rating-anomaly detector (S2) |
| Sales anomaly | ✅ | Flagged by the sales-anomaly detector (S2) |
| Spark/Python disagreement | ⬜ | Appears in the comparison report with an explanation (S2) |

## 7. Hidden-data readiness (SRS §1.8 items 8–9)

1. No test or module may hard-code IDs, item names or row counts, except the SRS minimums.
2. All paths come from `DINEIQ_DATA_DIR`.
3. Rehearse by generating an unseen dataset with a different seed and running everything against it:

```bash
python -m data_generator.run_generator --out hidden_sim --seed 2026
set DINEIQ_DATA_DIR=hidden_sim        # Windows   (Linux/macOS: export DINEIQ_DATA_DIR=hidden_sim)
pytest
```

Every module must run end-to-end on `hidden_sim`. Also rehearse: unknown menu items, new restaurant locations, price changes, unusual promotions, extreme wastage and outliers.

## 8. Surprise-modification rehearsal (SRS §1.8 item 5)

| Possible request | Tests that must be updated |
|---|---|
| Add a restaurant location / menu category | test_01 minimums stay valid; test_03 FKs must still pass |
| Change profitability thresholds | S2 classification tests |
| Add a feature / Spark transformation | S1 unit test with a small in-memory DataFrame |
| Modify the forecast window | S2 forecast tests (chronological split) |
| Add a KPI / anomaly rule / dashboard filter | The owner adds one test per rule or filter |

## 9. Exit criteria for submission

- All data-contract tests pass on the full dataset.
- Every ⬜ row in §5 is either implemented or explicitly listed as a limitation in the report.
- `reports/test_results/TEST_RESULTS.md` is regenerated on the final day and committed.

# Evidence Index

Owner: Student 6 · SRS v1.0 §1.10 items 4–8, 12, 14

**Rule:** no number goes into the report, blog, slides or video unless it comes from a file listed here. SRS §1.8 item 7 treats fabricated metrics and hard-coded insights as grounds for disqualification.

**Git caution:** `.gitignore` excludes `full_output/` and every `*.log` file. Copy the evidence you need into `reports/`, and save logs as `.txt`. Otherwise they will silently fail to commit.

Legend: ✅ in repo · ⏳ produced but not committed · ⬜ not produced

## 1. Dataset (item 3)

| Evidence | Path | Owner | Status |
|---|---|---|---|
| Generation scripts | `data_generator/` | S1 | ✅ |
| Data dictionary (MD + JSON) | `documentation/data_dictionary/` | S1 | ✅ (missing `launch_date`) |
| Dataset statistics | `reports/dataset/dataset_statistics.json` (copy from `full_output/reports/`) | S1 | ⏳ |
| Generation validation | `reports/dataset/data_generation_validation.json` | S1 | ⏳ |
| Raw / cleaned samples | `sample_data/raw/`, `sample_data/clean/` (`tests/tools/export_sample_data.py`) | S6 | ⬜ |
| Train / validation / test splits | `processed_data/splits/` + split description | S2 | ⬜ |

## 2. Spark processing (item 4): Student 1

| Evidence | Path | Status |
|---|---|---|
| Ingestion report (explicit and inferred schema, partitions) | `reports/spark/step3_ingestion_report.json` | ⏳ |
| Data-quality report | `reports/spark/data_quality_report.json` | ⏳ |
| Cleaning report and rules | `reports/spark/cleaning_report.json` | ⏳ |
| Feature-engineering report | `reports/spark/feature_engineering_report.json` | ⏳ |
| Spark SQL queries and outputs | `spark_sql/` + `reports/spark/sql_results/` | ⬜ |
| Partition strategy | `documentation/PROJECT_REPORT.md` §11 | ⬜ |
| Execution logs (saved as `.txt`) | `reports/spark/logs/*.txt` | ⬜ |
| Processing times | `reports/spark/processing_times.csv` | ⬜ |
| Independent quality cross-check | `reports/evidence/independent_quality_counts.json` (`python -m tests.quality_checks`) | S6 ⬜ |

## 3. Spark MLlib (item 5) and Python (item 6): Student 2

Required for each model:
- features used;
- algorithms tested (at least 3 in Spark);
- hyperparameters;
- train, validation and test results, with metrics and a confusion matrix;
- the saved model with its version;
- sample predictions.

| Evidence | Spark path | Python path |
|---|---|---|
| Metrics per algorithm | `reports/mllib/metrics.json` | `reports/python/metrics.json` |
| Confusion matrices | `reports/mllib/confusion_*.png` | `reports/python/confusion_*.png` |
| Saved models + version | `models/spark/<model>_v<N>/` | `models/python/<model>_v<N>.joblib` |
| Sample predictions | `reports/mllib/sample_predictions.csv` | `reports/python/sample_predictions.csv` |

## 4. Dual-pipeline comparison (item 7): Student 2

File: `reports/comparison/dual_pipeline_comparison.csv`, covering at least 100 **unseen** records. Required columns:

`record_id, actual, spark_result, python_result, match, numeric_difference, confidence, consistency_status, disagreement_explanation`

A summary in `reports/comparison/SUMMARY.md` gives the overall agreement percentage and explains the major disagreements.

## 5. Restaurant Intelligence report (item 8): Students 2/3

File: `reports/intelligence/RESTAURANT_INTELLIGENCE_REPORT.md`. Every figure in it must cite a result file.

## 6. Tests (item 9): Student 6

| Evidence | Path |
|---|---|
| JUnit XML | `reports/test_results/junit.xml` |
| Human-readable results | `reports/test_results/TEST_RESULTS.md` |

## 7. Screenshots (item 12)

Name screenshots `screenshots/NN_area_description.png`, for example `03_spark_quality_report.png` or `11_dual_pipeline_dashboard.png`. Capture:
- each Spark run;
- each dashboard;
- the what-if screen;
- the recommendation evidence panel;
- an export;
- a test run.

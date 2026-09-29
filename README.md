# 🌐 [اضغط هنا لزيارة الموقع المباشر (Live Demo)](https://r38683613-commits.github.io/Blog-Data-Miners/)
---
# DineIQ Analytics

**Theme:** MenuMatrix Dining Intelligence
**Category:** Data Science Intelligence Arena
**Specification:** DineIQ Analytics SRS v1.0

DineIQ Analytics is a web-based restaurant intelligence platform. It processes orders, menu items, pricing, customers, ratings, promotions, inventory and wastage with Apache Spark. It verifies selected results with an independent Python Data Science pipeline and turns both into evidence-based recommendations.

> **Status (2026-09-29):**
> - Complete: dataset generation (Step 1), CSV/Parquet storage (Step 2) and the data dictionary.
> - In progress: Spark ingestion, quality, cleaning and feature engineering (Steps 3–7).
> - Not yet in the repository: modules from Step 8 onward.
>
> Tracking: [documentation/SUBMISSION_CHECKLIST.md](documentation/SUBMISSION_CHECKLIST.md).

## Quick links

| Item | Link |
|---|---|
| Deployed application | _TBD: add URL_ |
| Demonstration video (.mp4) | _TBD: add link_ |
| Technical blog (at least 2,000 words) | _TBD: add link_ |
| Project report | [documentation/PROJECT_REPORT.md](documentation/PROJECT_REPORT.md) |
| Full dataset (about 270 MB, Google Drive) | [Download](https://drive.google.com/file/d/1yRC_9qfYSns0G7hck_vjQd9qOM57iCqP/view?usp=sharing) |
| Test results | [reports/test_results/TEST_RESULTS.md](reports/test_results/TEST_RESULTS.md) |
| AI usage declaration | [AI_USAGE.md](AI_USAGE.md) |

## 1. Dataset

The dataset is synthetic but realistic, with 12 interconnected tables: the 11 business tables from the SRS plus the `Promotion_Items` junction table. It is fully reproducible with seed 42.

| Measure | Delivered | SRS minimum |
|---|---|---|
| Order lines | 1,066,785 | 1,000,000 |
| Unique orders | 100,000 | 100,000 |
| Customers | 50,000 | 50,000 |
| Menu items / categories | 150 / 10 | 150 / 10 |
| Restaurant locations | 20 | 20 |
| Transaction history | 2024-01-01 to 2024-12-31 | 12 months |
| Ratings | 100,518 | 100,000 |
| Wastage records | 50,000 | 50,000 |
| Pricing-history records | 689 | multiple |
| Promotion campaigns | 30 | multiple |

The raw layer intentionally contains the 15 data-quality defects from SRS Step 4 and the 10 difficult business cases from Step 11. [PROJECT_REPORT.md §21–22](documentation/PROJECT_REPORT.md) explains how each one is generated. Column definitions are in [DATA_DICTIONARY.md](documentation/data_dictionary/DATA_DICTIONARY.md).

The full dataset is too large for GitHub. Download it from the link above and extract it so that `full_output/raw_data/` and `full_output/parquet_data/` exist at the repository root. Alternatively, regenerate it (section 5) or set `DINEIQ_DATA_DIR` to another location. Small samples live in `sample_data/`.

## 2. Team and modules

| Member | Module | Main folders |
|---|---|---|
| Student 1: _name_ | Data Engineering & Big Data Foundation (SRS Steps 1–7) | `data_generator/`, `spark_jobs/` |
| Student 2: _name_ | Data Science & ML: Spark MLlib, Python pipeline, dual-pipeline comparison | `spark_jobs/`, `python_pipeline/`, `models/` |
| Student 3: _name_ | Dashboards & Recommendation Engine | `src/`, `templates/`, `static/` |
| Student 4: _name_ | Backend API, authentication, export | `src/`, `database/` |
| Student 5: _name_ | _TBD_ | |
| Student 6: _name_ | Technical documentation, testing, evidence, submission | `documentation/`, `tests/`, `reports/`, `screenshots/` |

Every member must be able to explain their own module (SRS §1.8). See [TEAM_CONTRIBUTIONS.md](documentation/TEAM_CONTRIBUTIONS.md).

## 3. Repository structure

Legend: ✅ available · ⏳ in progress · ⬜ not started

```
├── README.md            project overview (this file)                    ✅
├── AI_USAGE.md          AI tool declaration                             ✅ every member adds rows
├── LICENSE                                                              ✅
├── requirements.txt     backend, export and test dependencies           ⏳ Spark deps not pinned
├── pytest.ini           test configuration                              ✅
├── data_generator/      dataset-generation scripts                      ✅
├── spark_jobs/          Spark ingestion, quality, cleaning, features    ⏳
├── spark_sql/           Spark SQL queries                               ⬜
├── python_pipeline/     independent Python Data Science pipeline        ⬜
├── models/              saved Spark and Python models                   ⬜
├── notebooks/           exploratory notebooks                           ⬜
├── src/ templates/ static/   web application                            ⬜
├── database/            database schema and setup                       ⬜
├── config/              configuration                                   ⬜
├── tests/               automated tests + evidence tools                ✅ data layer
├── sample_data/         raw and cleaned samples                         ⏳
├── documentation/       report, dictionary, plans, logs                 ⏳
├── reports/             generated reports and test results             ⏳
└── screenshots/         UI and pipeline evidence                        ⬜
```

## 4. Installation

Full instructions, including Java, Spark and Windows notes, are in [documentation/INSTALLATION.md](documentation/INSTALLATION.md). Short version:

```bash
git clone https://github.com/ismailalatar/dineiq-analytics-data-engineering.git
cd dineiq-analytics-data-engineering
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## 5. Running the project

| Task (SRS §1.10 item 11) | Command / location | Status |
|---|---|---|
| Generate the dataset (full, seed 42) | `python -m data_generator.run_generator --out full_output` | ✅ |
| Generate a small smoke dataset | `python -m data_generator.run_generator --test` | ✅ |
| Load the dataset (Spark ingestion) | `python -m spark_jobs.tests.test_u11_ingestion` (Spark venv) | ⏳ |
| Data-quality analysis | `python -m spark_jobs.tests.test_u12_quality` | ⏳ |
| Data cleaning | `python -m spark_jobs.tests.test_u13_cleaning` | ⏳ |
| Feature engineering | `python -m spark_jobs.tests.test_u14_features` | ⏳ |
| Execute Spark SQL | _Pending: Student 1_ | ⬜ |
| Train Spark / Python models, compare results | _Pending: Student 2_ | ⬜ |
| Menu analysis, segments, basket analysis, forecasts, wastage | _Pending: Student 2_ | ⬜ |
| What-if analysis, recommendations, dashboards | _Pending: Student 3_ | ⬜ |
| Log in, export reports | _Pending: Student 4_ | ⬜ |
| Run automated tests | `pytest` | ✅ |

## 6. Testing and evidence

```bash
pytest                                             # full suite (skips cleanly if data is absent)
python tests/tools/run_tests_with_report.py        # suite + JUnit XML + Markdown evidence report
python -m tests.quality_checks                     # independent pandas defect counts (JSON)
python tests/tools/export_sample_data.py           # refresh sample_data/ from the full dataset
```

- Test strategy and coverage: [documentation/testing/TEST_PLAN.md](documentation/testing/TEST_PLAN.md)
- Evidence index: [documentation/evidence/EVIDENCE_INDEX.md](documentation/evidence/EVIDENCE_INDEX.md)

## 7. Documentation index

| Document | Purpose |
|---|---|
| [PROJECT_REPORT.md](documentation/PROJECT_REPORT.md) | Full project report (SRS §1.10 item 1) |
| [INSTALLATION.md](documentation/INSTALLATION.md) | Installation and troubleshooting |
| [DATA_DICTIONARY.md](documentation/data_dictionary/DATA_DICTIONARY.md) | Tables, columns, keys |
| [TEST_PLAN.md](documentation/testing/TEST_PLAN.md) | Test strategy and test catalogue |
| [EVIDENCE_INDEX.md](documentation/evidence/EVIDENCE_INDEX.md) | Where every piece of evidence lives |
| [SUBMISSION_CHECKLIST.md](documentation/SUBMISSION_CHECKLIST.md) | Final submission tracking |
| [DEVELOPMENT_LOG.md](documentation/DEVELOPMENT_LOG.md) | Daily development log (SRS §1.8 item 3) |
| [TEAM_CONTRIBUTIONS.md](documentation/TEAM_CONTRIBUTIONS.md) | Who built what |

## 8. Evaluator access

| Role | Username | Password |
|---|---|---|
| Evaluator | _TBD_ | _TBD_ |
| Administrator | _TBD_ | _TBD_ |

Use demo-only accounts. Never commit real passwords or `.env` files.

## 9. Assumptions

- All data is synthetic. The 20 restaurant locations are named after cities in Yemen, and no real customers are included.
- Transaction history covers calendar year 2024, and all amounts are in a single currency.
- The hidden evaluation dataset follows the same 12-table schema and column names as the data dictionary.
- NFR 1 of the SRS mentions "uploaded claim details". We read this as "uploaded restaurant records", assuming a copy error in the specification.

## 10. Limitations

- One year of history gives only one observation of each season, which limits seasonal forecasting.
- Spark runs in local mode on a laptop, not on a cluster.
- The synthetic data follows designed patterns and is more regular than real POS data.

## 11. License

MIT. See [LICENSE](LICENSE).

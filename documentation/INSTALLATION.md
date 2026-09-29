# Installation Guide

This guide covers SRS v1.0 §1.10 item 10. Items marked **confirm** need a value from the module owner before submission.

## 1. Supported platforms

| Platform | Status | Notes |
|---|---|---|
| Windows 10/11 (64-bit) | Primary (team environment) | Spark needs `winutils.exe` to write files (see §4.2) |
| Ubuntu 22.04 / 24.04 | Expected to work | |
| macOS 13+ | Expected to work | |

Hardware requirements (SRS §1.9.1):
- Core i5 or better.
- At least 8 GB RAM; 16 GB is recommended for Spark on the full dataset.
- About 2 GB of free disk space for the dataset and Parquet output.

## 2. Prerequisites

| Software | Version | Check |
|---|---|---|
| Python | 3.10 or 3.11 (**confirm**) | `python --version` |
| Java JDK | 17 (supported by PySpark 3.5 and 4.x) | `java -version` |
| Git | recent | `git --version` |

Set `JAVA_HOME` to the JDK folder. Then add `%JAVA_HOME%\bin` (Windows) or `$JAVA_HOME/bin` (Linux/macOS) to `PATH`.

## 3. Get the code

```bash
git clone https://github.com/ismailalatar/dineiq-analytics-data-engineering.git
cd dineiq-analytics-data-engineering
```

## 4. Virtual environments

The team keeps Spark in a separate environment. See the comment in `requirements.txt`.

### 4.1 Application and tests: `.venv`

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
```

### 4.2 Spark: `.venv_spark`

```bash
python -m venv .venv_spark
.venv_spark\Scripts\activate    # Windows
pip install pyspark==<VERSION> pandas pyarrow    # confirm VERSION with Student 1
```

- **To do (Student 1):** commit `requirements-spark.txt` so evaluators can reproduce the exact Spark stack.
- Set `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` to the Python inside `.venv_spark`.
- **Windows only:** Spark fails when writing Parquet unless the Hadoop helper files are installed.
  1. Place a Hadoop 3.x build of `winutils.exe` and `hadoop.dll` in `C:\hadoop\bin`.
  2. Set `HADOOP_HOME=C:\hadoop`.
  3. Add `%HADOOP_HOME%\bin` to `PATH`.

## 5. Dataset

- **Option A (download):** get the archive from the README link. Extract it so that `full_output/raw_data/` and `full_output/parquet_data/` exist at the repository root.
- **Option B (regenerate):** run `python -m data_generator.run_generator --out full_output`. The default seed is 42, and the run takes a few minutes. It also writes `full_output/reports/data_generation_validation.json` and `dataset_statistics.json`.
- **Smoke dataset:** run `python -m data_generator.run_generator --test`. It writes a small dataset to `smoke_output/` in seconds, which is useful for quick checks. Volume tests will fail on it by design.
- **Other location:** set `DINEIQ_DATA_DIR` to the folder that contains `raw_data/`.

## 6. Database setup

_Pending: Student 4 (engine, schema script, seed users)._

## 7. Spark processing

```bash
.venv_spark\Scripts\activate
python -m spark_jobs.tests.test_u11_ingestion
python -m spark_jobs.tests.test_u12_quality
python -m spark_jobs.tests.test_u13_cleaning
python -m spark_jobs.tests.test_u14_features
```

## 8. Python pipeline and web application

_Pending: Student 2 (pipeline) and Students 3/4 (web app)._

## 9. Automated tests

```bash
.venv\Scripts\activate
pytest
python tests/tools/run_tests_with_report.py
```

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `JAVA_HOME is not set` / `Java gateway process exited` | Java missing or not on PATH | Install JDK 17 and set `JAVA_HOME` |
| `Python worker failed to connect back` | Spark uses a different Python | Set `PYSPARK_PYTHON` to the venv Python |
| `HADOOP_HOME and hadoop.home.dir are unset` (Windows) | winutils missing | See §4.2 |
| `java.lang.OutOfMemoryError` | Default driver memory too small | Set `spark.driver.memory` to `4g` or more |
| All data tests show `SKIPPED` | Dataset not found | Extract it to `full_output/` or set `DINEIQ_DATA_DIR` |
| `FileNotFoundError: Table 'X' not found` | File named differently | File names must match table names (case-insensitive) |

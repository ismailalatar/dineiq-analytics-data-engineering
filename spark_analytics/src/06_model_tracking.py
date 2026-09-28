import os
import csv
import glob
import shutil
from datetime import datetime

# ============================================================
# Windows / PySpark environment
# ============================================================

PYTHON_EXE = r"C:\Users\acer\AppData\Local\Programs\Python\Python312\python.exe"

os.environ["PYSPARK_PYTHON"] = PYTHON_EXE
os.environ["PYSPARK_DRIVER_PYTHON"] = PYTHON_EXE
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["hadoop.home.dir"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ["PATH"]

from pyspark.sql import SparkSession


# ============================================================
# Project paths
# ============================================================

BASE = r"D:\DineIQ"
SPARK_DIR = os.path.join(BASE, "spark_analytics")
RESULTS_DIR = os.path.join(SPARK_DIR, "results")

metrics_dir = os.path.join(
    RESULTS_DIR,
    "mllib_model_metrics.csv"
)

registry_path = os.path.join(
    RESULTS_DIR,
    "model_registry.csv"
)


# ============================================================
# Start Spark
# ============================================================

spark = (
    SparkSession.builder
    .appName("DineIQ Model Version Tracking")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 70)
print("DINEIQ - MODEL VERSION TRACKING")
print("=" * 70)

print("\nSpark version:", spark.version)


# ============================================================
# Locate current MLlib metrics
# ============================================================

part_files = glob.glob(
    os.path.join(metrics_dir, "part-*.csv")
)

if not part_files:
    raise FileNotFoundError(
        "Current MLlib metrics were not found: "
        + metrics_dir
    )

metrics_file = part_files[0]

print("\nCurrent metrics file:")
print(metrics_file)


# ============================================================
# Read current MLlib metrics
# ============================================================

with open(
    metrics_file,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)
    metrics_rows = list(reader)


if not metrics_rows:
    raise ValueError(
        "MLlib metrics file is empty."
    )


print("\nModels found:", len(metrics_rows))


# ============================================================
# Build current model registry
# ============================================================

registry_rows = []

tracking_timestamp = datetime.now().astimezone().isoformat(
    timespec="seconds"
)

for row in metrics_rows:

    registry_rows.append(
        {
            "model_version": row["model_version"],
            "model": row["model"],
            "dataset_version": row["dataset_version"],
            "feature_version": row["feature_version"],
            "classification_target": "menu_class",
            "feature_source": os.path.join(
                RESULTS_DIR,
                "menu_classification.parquet"
            ),
            "training_date": row["training_date"],
            "parameters": row["parameters"],
            "train_rows": row["train_rows"],
            "validation_rows": row["validation_rows"],
            "test_rows": row["test_rows"],
            "validation_accuracy": row["validation_accuracy"],
            "validation_f1": row["validation_f1"],
            "validation_precision": row["validation_precision"],
            "validation_recall": row["validation_recall"],
            "test_accuracy": row["test_accuracy"],
            "test_f1": row["test_f1"],
            "test_precision": row["test_precision"],
            "test_recall": row["test_recall"],
            "spark_version": spark.version,
            "saved_model_path": row["saved_model_path"],
            "tracking_timestamp": tracking_timestamp
        }
    )


# ============================================================
# Display registry
# ============================================================

print("\n" + "=" * 70)
print("CURRENT MODEL REGISTRY")
print("=" * 70)

for row in registry_rows:

    print("\nModel:", row["model"])
    print("Version:", row["model_version"])
    print("Dataset:", row["dataset_version"])
    print("Feature Version:", row["feature_version"])
    print("Training Date:", row["training_date"])
    print("Train / Validation / Test:",
          row["train_rows"],
          "/",
          row["validation_rows"],
          "/",
          row["test_rows"])
    print("Validation Accuracy:", row["validation_accuracy"])
    print("Validation F1:", row["validation_f1"])
    print("Test Accuracy:", row["test_accuracy"])
    print("Test F1:", row["test_f1"])
    print("Parameters:", row["parameters"])
    print("Model Path:", row["saved_model_path"])


# ============================================================
# Remove stale registry
# ============================================================

if os.path.isdir(registry_path):
    print("\nRemoving old registry directory...")
    shutil.rmtree(registry_path)

elif os.path.isfile(registry_path):
    print("\nRemoving old registry file...")
    os.remove(registry_path)


# ============================================================
# Write SINGLE CSV registry file
# ============================================================

fieldnames = [
    "model_version",
    "model",
    "dataset_version",
    "feature_version",
    "classification_target",
    "feature_source",
    "training_date",
    "parameters",
    "train_rows",
    "validation_rows",
    "test_rows",
    "validation_accuracy",
    "validation_f1",
    "validation_precision",
    "validation_recall",
    "test_accuracy",
    "test_f1",
    "test_precision",
    "test_recall",
    "spark_version",
    "saved_model_path",
    "tracking_timestamp"
]

with open(
    registry_path,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(registry_rows)


# ============================================================
# Final summary
# ============================================================

print("\n" + "=" * 70)
print("TRACKING SUMMARY")
print("=" * 70)

print("Tracked models:", len(registry_rows))
print("Registry version:", registry_rows[0]["model_version"])
print("Dataset version:", registry_rows[0]["dataset_version"])
print("Feature version:", registry_rows[0]["feature_version"])

print("\nRegistry saved to:")
print(registry_path)

print("\nModel version tracking completed successfully.")

spark.stop()

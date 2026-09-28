import os
import shutil
import csv

# ============================================================
# Environment
# ============================================================

PYTHON_EXE = r"C:\Users\acer\AppData\Local\Programs\Python\Python312\python.exe"

os.environ["PYSPARK_PYTHON"] = PYTHON_EXE
os.environ["PYSPARK_DRIVER_PYTHON"] = PYTHON_EXE
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["hadoop.home.dir"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ["PATH"]

from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel


# ============================================================
# Project paths
# ============================================================

BASE_DIR = r"D:\DineIQ"

DATA_PATH = os.path.join(
    BASE_DIR,
    "spark_analytics",
    "results",
    "menu_classification.parquet"
)

MODELS_DIR = os.path.join(
    BASE_DIR,
    "spark_analytics",
    "models"
)

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "spark_analytics",
    "results",
    "model_verification.csv"
)


# ============================================================
# Start Spark
# ============================================================

spark = (
    SparkSession.builder
    .appName("DineIQ Model Verification")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


print("=" * 60)
print("DINEIQ - MODEL SAVE / LOAD VERIFICATION")
print("=" * 60)

print("\nSpark version:", spark.version)
print("Dataset:", DATA_PATH)
print("Models directory:", MODELS_DIR)


# ============================================================
# Check input dataset
# ============================================================

if not os.path.exists(DATA_PATH):
    print("\nERROR: Dataset not found:")
    print(DATA_PATH)
    spark.stop()
    raise SystemExit(1)


# ============================================================
# Read classification dataset
# ============================================================

df = spark.read.parquet(DATA_PATH)

dataset_rows = df.count()

print("\nDataset rows:", dataset_rows)


# ============================================================
# Saved model paths
# ============================================================

model_paths = {
    "Logistic Regression": os.path.join(
        MODELS_DIR,
        "logistic_regression"
    ),

    "Decision Tree": os.path.join(
        MODELS_DIR,
        "decision_tree"
    ),

    "Random Forest": os.path.join(
        MODELS_DIR,
        "random_forest"
    )
}


verification_rows = []


# ============================================================
# Verify each saved model
# ============================================================

for model_name, model_path in model_paths.items():

    print("\n" + "=" * 60)
    print("MODEL:", model_name)
    print("Path:", model_path)
    print("=" * 60)

    if not os.path.exists(model_path):

        print("STATUS: NOT FOUND")

        verification_rows.append({
            "model": model_name,
            "model_path": model_path,
            "load_success": False,
            "prediction_rows": 0,
            "dataset_rows": dataset_rows,
            "status": "NOT FOUND",
            "verification_message": "Saved model directory does not exist."
        })

        continue

    try:

        # ----------------------------------------------------
        # Load saved PipelineModel
        # ----------------------------------------------------

        model = PipelineModel.load(model_path)

        print("Model loaded successfully.")

        # ----------------------------------------------------
        # Generate predictions
        # ----------------------------------------------------

        predictions = model.transform(df)

        prediction_count = predictions.count()

        print("Prediction rows:", prediction_count)

        # ----------------------------------------------------
        # Display sample predictions
        # ----------------------------------------------------

        predictions.select(
            "menu_class",
            "prediction"
        ).show(5, truncate=False)

        # ----------------------------------------------------
        # Verify prediction count
        # ----------------------------------------------------

        if prediction_count == dataset_rows:

            status = "VERIFIED"

            message = (
                "Model loaded successfully and prediction "
                "count matches dataset row count."
            )

            print("STATUS: VERIFIED")

        else:

            status = "FAILED"

            message = (
                "Model loaded, but prediction count does "
                "not match dataset row count."
            )

            print("STATUS: FAILED")
            print(message)

        verification_rows.append({
            "model": model_name,
            "model_path": model_path,
            "load_success": True,
            "prediction_rows": prediction_count,
            "dataset_rows": dataset_rows,
            "status": status,
            "verification_message": message
        })

    except Exception as e:

        print("STATUS: FAILED")
        print("ERROR:", str(e))

        verification_rows.append({
            "model": model_name,
            "model_path": model_path,
            "load_success": False,
            "prediction_rows": 0,
            "dataset_rows": dataset_rows,
            "status": "FAILED",
            "verification_message": str(e)
        })


# ============================================================
# Verification summary
# ============================================================

print("\n")
print("=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)

for row in verification_rows:

    print(
        f"{row['model']}: "
        f"{row['status']} | "
        f"Predictions={row['prediction_rows']} | "
        f"Dataset={row['dataset_rows']}"
    )


verified_count = sum(
    1
    for row in verification_rows
    if row["status"] == "VERIFIED"
)

print("\nVerified models:", verified_count, "/", len(model_paths))


# ============================================================
# Save verification results as a single CSV file
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

if os.path.isdir(OUTPUT_PATH):
    shutil.rmtree(OUTPUT_PATH)

elif os.path.isfile(OUTPUT_PATH):
    os.remove(OUTPUT_PATH)


fieldnames = [
    "model",
    "model_path",
    "load_success",
    "prediction_rows",
    "dataset_rows",
    "status",
    "verification_message"
]


with open(
    OUTPUT_PATH,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(verification_rows)


# ============================================================
# Finish
# ============================================================

print("\nVerification results saved to:")
print(OUTPUT_PATH)

print("\nModel save/load verification completed successfully.")

spark.stop()

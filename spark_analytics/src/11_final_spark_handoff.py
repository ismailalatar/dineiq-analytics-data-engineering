from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
import os

BASE_DIR = r"D:\DineIQ"

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "student2",
    "results"
)

OUTPUT_PATH = os.path.join(
    RESULTS_DIR,
    "spark_handoff_summary.csv"
)

spark = (
    SparkSession.builder
    .appName("DineIQ Final Spark Handoff")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("DINEIQ - FINAL SPARK HANDOFF")

records = []

metrics_path = os.path.join(
    RESULTS_DIR,
    "mllib_model_metrics.csv"
)

if os.path.exists(metrics_path):

    metrics = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(metrics_path)
    )

    print("\nMLlib Results:")
    metrics.show(truncate=False)

    for row in metrics.collect():
        records.append(
            (
                "MLlib Classification",
                row["model"],
                str(row["accuracy"]),
                str(row["f1_score"]),
                "Completed"
            )
        )

forecast_path = os.path.join(
    RESULTS_DIR,
    "forecast_metrics.csv"
)

if os.path.exists(forecast_path):

    forecast = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(forecast_path)
    )

    print("\nForecast Results:")
    forecast.show(truncate=False)

    row = forecast.first()

    records.append(
        (
            "Revenue Forecasting",
            "Linear Regression",
            str(row["MAE"]),
            str(row["RMSE"]),
            "Completed"
        )
    )

verification_path = os.path.join(
    RESULTS_DIR,
    "model_verification.csv"
)

if os.path.exists(verification_path):

    verification = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(verification_path)
    )

    print("\nModel Verification:")
    verification.show(truncate=False)

    verified_count = verification.filter(
        verification.load_success == True
    ).count()

    records.append(
        (
            "Model Verification",
            "Saved Models",
            str(verified_count),
            str(verification.count()),
            "Completed"
        )
    )

if records:

    summary = spark.createDataFrame(
        records,
        [
            "component",
            "model_or_method",
            "metric_1",
            "metric_2",
            "status"
        ]
    )

    summary = summary.withColumn(
        "generated_at",
        current_timestamp()
    )

    print("\nFinal Handoff Summary:")
    summary.show(truncate=False)

    (
        summary
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header", "true")
        .csv(OUTPUT_PATH)
    )

    print("\nHandoff summary saved to:")
    print(OUTPUT_PATH)

else:
    print("\nNo previous result files were found.")

print("\nFinal Spark handoff completed.")

spark.stop()
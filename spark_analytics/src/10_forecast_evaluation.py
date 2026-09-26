from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    abs as spark_abs,
    sqrt,
    pow,
    avg,
    when
)
import os

BASE_DIR = r"D:\DineIQ"

INPUT_PATH = os.path.join(
    BASE_DIR,
    "student2",
    "results",
    "forecast_results.parquet"
)

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "student2",
    "results",
    "forecast_metrics.csv"
)

spark = (
    SparkSession.builder
    .appName("DineIQ Forecast Evaluation")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("DINEIQ - FORECAST EVALUATION")

df = spark.read.parquet(INPUT_PATH)

print("Forecast rows:", df.count())

evaluated = (
    df
    .withColumn(
        "absolute_error",
        spark_abs(col("revenue") - col("prediction"))
    )
    .withColumn(
        "squared_error",
        pow(
            col("revenue") - col("prediction"),
            2
        )
    )
    .withColumn(
        "percentage_error",
        when(
            col("revenue") != 0,
            spark_abs(
                (col("revenue") - col("prediction"))
                / col("revenue")
            ) * 100
        )
    )
)

metrics = evaluated.select(
    avg("absolute_error").alias("MAE"),
    sqrt(avg("squared_error")).alias("RMSE"),
    avg("percentage_error").alias("MAPE")
)

print("\nForecast metrics:")
metrics.show(truncate=False)

metrics.write.mode("overwrite") \
    .option("header", "true") \
    .csv(OUTPUT_PATH)

print("\nForecast metrics saved to:")
print(OUTPUT_PATH)

print("\nForecast evaluation completed successfully.")

spark.stop()
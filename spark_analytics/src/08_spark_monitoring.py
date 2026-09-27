from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, count
from datetime import datetime
import json
import os

# Project paths
base_dir = r"D:\DineIQ"

data_path = os.path.join(
    base_dir,
    "full_output",
    "processed_data",
    "features",
    "order_features.parquet"
)

log_path = os.path.join(
    base_dir,
    "student2",
    "results",
    "spark_execution_log.json"
)

# Record the start time
start_time = datetime.now()

# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Spark Monitoring")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 50)
print("DINEIQ - SPARK JOB MONITORING")
print("=" * 50)

# Get Spark application information
sc = spark.sparkContext
print("\nApplication ID:", sc.applicationId)
print("Application Name:", sc.appName)
print("Spark Version:", spark.version)

# Read the input dataset
df = spark.read.parquet(data_path)
row_count = df.count()

print("\nInput rows:", row_count)

# Calculate completed orders and revenue by restaurant
summary = (
    df.filter(col("order_status") == "completed")
    .groupBy("restaurant_id")
    .agg(
        count("*").alias("completed_orders"),
        spark_sum("order_total").alias("revenue")
    )
    .orderBy(col("revenue").desc())
)

print("\nCompleted orders by restaurant:")
summary.show(10)

# Calculate the job execution time
end_time = datetime.now()
duration_seconds = (
    end_time - start_time
).total_seconds()

# Store execution information
execution_info = {
    "application_id": sc.applicationId,
    "application_name": sc.appName,
    "spark_version": spark.version,
    "input_path": data_path,
    "input_rows": row_count,
    "start_time": start_time.isoformat(),
    "end_time": end_time.isoformat(),
    "duration_seconds": duration_seconds,
    "operation": "Completed order aggregation by restaurant"
}

# Save the execution log
with open(log_path, "w", encoding="utf-8") as f:
    json.dump(execution_info, f, indent=4)

print("\nEXECUTION EVIDENCE")
print("=" * 50)

# Show the execution details
for key, value in execution_info.items():
    print(key + ":", value)

print("\nExecution log saved to:")
print(log_path)

print("\nSpark monitoring completed.")

spark.stop()
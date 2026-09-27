from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp, when
import os
# Project and results paths
base_dir = r"D:\DineIQ"
results_dir = os.path.join(base_dir, "student2", "results")
metrics_path = os.path.join(
    results_dir,
    "mllib_model_metrics.csv"
)

registry_path = os.path.join(
    results_dir,
    "model_registry.csv"
)

# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Model Tracking")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")
print("=" * 50)
print("DINEIQ - MODEL TRACKING")
print("=" * 50)
print("\nSpark version:", spark.version)

# Read the model metrics
metrics_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(metrics_path)
)
print("\nMetrics rows:", metrics_df.count())
metrics_df.show(truncate=False)

# Add tracking information to the model metrics
registry_df = (
    metrics_df
    .withColumn("model_version", lit("v1.0"))
    .withColumn("dataset_version", lit("DineIQ-2024-v1"))
    .withColumn("classification_target", lit("menu_class"))
    .withColumn(
        "feature_source",
        lit(r"D:\DineIQ\student2\results\menu_classification.parquet")
    )
    .withColumn(
        "models_directory",
        lit(r"D:\DineIQ\student2\results\models")
    )
    .withColumn("spark_version", lit(spark.version))
    .withColumn("tracking_timestamp", current_timestamp())
)
# Add the saved path for each model
registry_df = registry_df.withColumn(
    "saved_model_path",
    when(
        registry_df.model == "Logistic Regression",
        lit(r"D:\DineIQ\student2\results\models\logistic_regression")
    )
    .when(
        registry_df.model == "Decision Tree",
        lit(r"D:\DineIQ\student2\results\models\decision_tree")
    )
    .when(
        registry_df.model == "Random Forest",
        lit(r"D:\DineIQ\student2\results\models\random_forest")
    )
    .otherwise(lit("UNKNOWN"))
)
# Select the columns for the model registry
columns = [
    "model_version",
    "model",
    "dataset_version",
    "classification_target",
    "feature_source",
    "train_rows",
    "test_rows",
    "accuracy",
    "f1_score",
    "weighted_precision",
    "weighted_recall",
    "spark_version",
    "saved_model_path",
    "tracking_timestamp"

]

registry_df = registry_df.select(*columns)
print("\nMODEL REGISTRY")
print("=" * 50)
registry_df.orderBy("model").show(truncate=False)
# Save the model registry
registry_df.coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(registry_path)

print("\nModel registry saved to:")

print(registry_path)

print("\nModel tracking completed.")

spark.stop()
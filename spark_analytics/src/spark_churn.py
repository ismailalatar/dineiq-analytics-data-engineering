from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.feature import VectorAssembler

import os

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("DineIQ_Spark_Churn")
    .getOrCreate()
)


# Training data
train_path = r"D:\DineIQ\python_analytics\python_pipeline\results\parquet\11_churn\churn_dataset.parquet"

# Test data: exactly the same 100 cases
test_path = r"D:\DineIQ\dual_test_cases.parquet"


# Required churn features
feat_cols = [
    "recency",
    "frequency",
    "monetary",
    "aov",
    "distinct_items",
    "r_score",
    "f_score",
    "m_score",
    "promo_sensitivity",
    "peak_ratio",
    "weekend_ratio"
]


print("Reading training data...")
train = spark.read.parquet(train_path)

print("Training rows:", train.count())


# Assemble features
assembler = VectorAssembler(
    inputCols=feat_cols,
    outputCol="features"
)

train_ready = assembler.transform(train)


# Spark Random Forest model
rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="churn",
    numTrees=300,
    maxDepth=12,
    seed=42
)


print("Training Spark Random Forest...")
model = rf.fit(train_ready)

print("Training completed.")


# Read exact 100 test cases
test = spark.read.parquet(test_path)

print("Test rows:", test.count())


# Generate predictions
test_ready = assembler.transform(test)

preds = model.transform(test_ready)


# Extract Spark probability
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col

preds = preds.withColumn(
    "spark_probability",
    vector_to_array(col("probability"))[1].cast("float")
)


# Select required output columns
result = preds.select(
    col("record_id"),
    col("churn"),
    col("prediction").alias("spark_prediction"),
    col("spark_probability")
)


# Required output
output_path = r"D:\DineIQ\python_analytics\python_pipeline\external\spark_forecast_results.parquet"


# Convert Spark result to Pandas
print("Converting Spark predictions to Pandas...")
result_pd = result.toPandas()


# Remove old output if it exists
if os.path.exists(output_path):
    os.remove(output_path)


# Save as Parquet using PyArrow
print("Saving Spark predictions as Parquet...")
result_pd.to_parquet(
    output_path,
    engine="pyarrow",
    index=False
)


print("Spark churn results saved to:")
print(output_path)

print("Result rows:", len(result_pd))


spark.stop()
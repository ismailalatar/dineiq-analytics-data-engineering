import os

PYTHON_EXE = r"C:\Users\acer\AppData\Local\Programs\Python\Python312\python.exe"

os.environ["PYSPARK_PYTHON"] = PYTHON_EXE
os.environ["PYSPARK_DRIVER_PYTHON"] = PYTHON_EXE

os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["hadoop.home.dir"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ["PATH"]

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler, Imputer
from pyspark.ml.classification import (
    LogisticRegression,
    DecisionTreeClassifier,
    RandomForestClassifier
)
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
import os
import shutil
from datetime import datetime


# ============================================================
# Spark
# ============================================================

spark = (
    SparkSession.builder
    .appName("DineIQ MLlib Menu Classification")
    .master("local[*]")
    .config("spark.hadoop.hadoop.home.dir", "C:\\")
    .config("spark.hadoop.io.native.lib.available", "false")
    .config("spark.hadoop.native.lib", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# ============================================================
# Paths
# ============================================================

BASE = r"D:\DineIQ"
SPARK_DIR = os.path.join(BASE, "spark_analytics")

input_path = os.path.join(
    SPARK_DIR, "results", "menu_classification.parquet"
)

model_base_path = os.path.join(
    SPARK_DIR, "models"
)

metrics_path = os.path.join(
    SPARK_DIR, "results", "mllib_model_metrics.csv"
)


# ============================================================
# Load dataset
# ============================================================

df = spark.read.parquet(input_path)

print("\nDINEIQ - SPARK MLLIB MENU CLASSIFICATION")
print("=" * 60)
print("Spark version:", spark.version)
print("Dataset:", input_path)
print("Total menu items:", df.count())


# ============================================================
# Target distribution
# ============================================================

print("\nTARGET DISTRIBUTION")

df.groupBy("menu_class") \
    .count() \
    .orderBy("menu_class") \
    .show(truncate=False)


# ============================================================
# Features
# ============================================================

numeric_features = [
    "cost",
    "order_frequency",
    "distinct_customers",
    "line_count",
    "avg_rating",
    "rating_count",
    "total_consumption",
    "total_wasted",
    "total_wastage_cost",
    "discount_total",
    "max_price",
    "min_price",
    "qty_promoted",
    "repeat_customers",
    "early_rating",
    "recent_rating",
    "wastage_pct",
    "promotion_dependency"
]

categorical_features = ["category_name"]

required_columns = (
    numeric_features
    + categorical_features
    + ["menu_class"]
)

missing_columns = [
    c for c in required_columns
    if c not in df.columns
]

if missing_columns:
    print("\nERROR - Missing columns:")
    print(missing_columns)
    spark.stop()
    raise SystemExit(1)


# Remove rows without target
df = df.filter(col("menu_class").isNotNull())


# ============================================================
# Preprocessing
# ============================================================

label_indexer = StringIndexer(
    inputCol="menu_class",
    outputCol="label",
    handleInvalid="keep"
)

category_indexer = StringIndexer(
    inputCol="category_name",
    outputCol="category_index",
    handleInvalid="keep"
)

category_encoder = OneHotEncoder(
    inputCol="category_index",
    outputCol="category_vector"
)

imputed_features = [
    f"{c}_imputed"
    for c in numeric_features
]

imputer = Imputer(
    inputCols=numeric_features,
    outputCols=imputed_features
)

assembler = VectorAssembler(
    inputCols=imputed_features + ["category_vector"],
    outputCol="features",
    handleInvalid="keep"
)


# ============================================================
# Train / Validation / Test
# ============================================================

train, validation, test = df.randomSplit(
    [0.70, 0.15, 0.15],
    seed=42
)

train_count = train.count()
validation_count = validation.count()
test_count = test.count()

print("\nDATA SPLIT")
print("=" * 60)
print("Training rows:", train_count)
print("Validation rows:", validation_count)
print("Testing rows:", test_count)


# ============================================================
# Models
# ============================================================

models = {
    "Logistic Regression": LogisticRegression(
        featuresCol="features",
        labelCol="label",
        maxIter=100
    ),

    "Decision Tree": DecisionTreeClassifier(
        featuresCol="features",
        labelCol="label",
        maxDepth=5,
        seed=42
    ),

    "Random Forest": RandomForestClassifier(
        featuresCol="features",
        labelCol="label",
        numTrees=50,
        maxDepth=6,
        seed=42
    )
}


# ============================================================
# Evaluators
# ============================================================

evaluators = {
    "accuracy": MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="accuracy"
    ),

    "f1": MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="f1"
    ),

    "precision": MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="weightedPrecision"
    ),

    "recall": MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="weightedRecall"
    )
}


# ============================================================
# Train, Validation, Test
# ============================================================

results = []

os.makedirs(model_base_path, exist_ok=True)

training_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for model_name, model in models.items():

    print("\n" + "=" * 60)
    print("MODEL:", model_name)
    print("=" * 60)

    pipeline = Pipeline(
        stages=[
            label_indexer,
            category_indexer,
            category_encoder,
            imputer,
            assembler,
            model
        ]
    )

    print("\nTraining model...")
    fitted_model = pipeline.fit(train)

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation_predictions = fitted_model.transform(validation)

    val_accuracy = evaluators["accuracy"].evaluate(
        validation_predictions
    )

    val_f1 = evaluators["f1"].evaluate(
        validation_predictions
    )

    val_precision = evaluators["precision"].evaluate(
        validation_predictions
    )

    val_recall = evaluators["recall"].evaluate(
        validation_predictions
    )

    print("\nVALIDATION")
    print("Accuracy:", round(val_accuracy, 4))
    print("F1 Score:", round(val_f1, 4))
    print("Precision:", round(val_precision, 4))
    print("Recall:", round(val_recall, 4))

    # --------------------------------------------------------
    # Final Test
    # --------------------------------------------------------

    test_predictions = fitted_model.transform(test)

    test_accuracy = evaluators["accuracy"].evaluate(
        test_predictions
    )

    test_f1 = evaluators["f1"].evaluate(
        test_predictions
    )

    test_precision = evaluators["precision"].evaluate(
        test_predictions
    )

    test_recall = evaluators["recall"].evaluate(
        test_predictions
    )

    print("\nFINAL TEST")
    print("Accuracy:", round(test_accuracy, 4))
    print("F1 Score:", round(test_f1, 4))
    print("Precision:", round(test_precision, 4))
    print("Recall:", round(test_recall, 4))

    # --------------------------------------------------------
    # Confusion Matrix
    # --------------------------------------------------------

    print("\nCONFUSION MATRIX")

    test_predictions.groupBy(
        "label",
        "prediction"
    ).count().orderBy(
        "label",
        "prediction"
    ).show()

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    safe_name = model_name.lower().replace(" ", "_")

    model_path = os.path.join(
        model_base_path,
        safe_name
    )

    if os.path.exists(model_path):
        shutil.rmtree(model_path)

    fitted_model.write().overwrite().save(model_path)

    print("Model saved to:", model_path)

    # --------------------------------------------------------
    # Model parameters
    # --------------------------------------------------------

    if model_name == "Logistic Regression":
        parameters = "maxIter=100"

    elif model_name == "Decision Tree":
        parameters = "maxDepth=5, seed=42"

    else:
        parameters = "numTrees=50, maxDepth=6, seed=42"

    # --------------------------------------------------------
    # Store results
    # --------------------------------------------------------

    results.append(
        (
            model_name,

            "v1.1",

            "DineIQ-2024-v1",

            "features-v1",

            training_date,

            parameters,

            train_count,
            validation_count,
            test_count,

            float(val_accuracy),
            float(val_f1),
            float(val_precision),
            float(val_recall),

            float(test_accuracy),
            float(test_f1),
            float(test_precision),
            float(test_recall),

            model_path
        )
    )


# ============================================================
# Metrics DataFrame
# ============================================================

metrics_df = spark.createDataFrame(
    results,
    [
        "model",
        "model_version",
        "dataset_version",
        "feature_version",
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

        "saved_model_path"
    ]
)


# ============================================================
# Model Comparison
# ============================================================

print("\n")
print("=" * 60)
print("MODEL COMPARISON - VALIDATION")
print("=" * 60)

metrics_df.orderBy(
    col("validation_f1").desc()
).select(
    "model",
    "validation_accuracy",
    "validation_f1",
    "validation_precision",
    "validation_recall"
).show(truncate=False)


print("=" * 60)
print("MODEL COMPARISON - FINAL TEST")
print("=" * 60)

metrics_df.orderBy(
    col("test_f1").desc()
).select(
    "model",
    "test_accuracy",
    "test_f1",
    "test_precision",
    "test_recall"
).show(truncate=False)


# ============================================================
# Save metrics
# ============================================================

if os.path.isdir(metrics_path):
    shutil.rmtree(metrics_path)
elif os.path.isfile(metrics_path):
    os.remove(metrics_path)

metrics_df.coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(metrics_path)

print("\nMetrics saved to:")
print(metrics_path)

print("\nSpark MLlib classification completed successfully.")

spark.stop()

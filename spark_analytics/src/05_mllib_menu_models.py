from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler, Imputer
from pyspark.ml.classification import LogisticRegression, DecisionTreeClassifier, RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


spark = (
    SparkSession.builder
    .appName("DineIQ MLlib Menu Classification")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


input_path = r"D:\DineIQ\student2\results\menu_classification.parquet"
model_base_path = r"D:\DineIQ\student2\results\models"
metrics_path = r"D:\DineIQ\student2\results\mllib_model_metrics.csv"


df = spark.read.parquet(input_path)

print("\nDINEIQ - SPARK MLLIB MENU CLASSIFICATION")
print("=" * 50)
print("Total menu items:", df.count())


print("\nTarget distribution")

df.groupBy("menu_class") \
    .count() \
    .orderBy("menu_class") \
    .show(truncate=False)


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

required_columns = numeric_features + categorical_features + ["menu_class"]

missing_columns = [
    c for c in required_columns
    if c not in df.columns
]

if missing_columns:
    print("\nMissing columns:")
    print(missing_columns)
    spark.stop()
    raise SystemExit(1)


df = df.filter(col("menu_class").isNotNull())


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


train, test = df.randomSplit([0.8, 0.2], seed=42)

train_count = train.count()
test_count = test.count()

print("\nTrain / Test")
print("Training rows:", train_count)
print("Testing rows:", test_count)


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


results = []

for model_name, model in models.items():

    print("\nMODEL:", model_name)
    print("-" * 40)

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

    fitted_model = pipeline.fit(train)
    predictions = fitted_model.transform(test)

    accuracy = evaluators["accuracy"].evaluate(predictions)
    f1 = evaluators["f1"].evaluate(predictions)
    precision = evaluators["precision"].evaluate(predictions)
    recall = evaluators["recall"].evaluate(predictions)

    print("Accuracy:", round(accuracy, 4))
    print("F1 Score:", round(f1, 4))
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))

    print("\nConfusion Matrix")

    predictions.groupBy(
        "label", "prediction"
    ).count().orderBy(
        "label", "prediction"
    ).show()

    safe_name = model_name.lower().replace(" ", "_")
    model_path = f"{model_base_path}/{safe_name}"

    fitted_model.write().overwrite().save(model_path)

    print("Model saved to:", model_path)

    results.append((
        model_name,
        float(accuracy),
        float(f1),
        float(precision),
        float(recall),
        int(train_count),
        int(test_count)
    ))


metrics_df = spark.createDataFrame(
    results,
    [
        "model",
        "accuracy",
        "f1_score",
        "weighted_precision",
        "weighted_recall",
        "train_rows",
        "test_rows"
    ]
)


print("\nMODEL COMPARISON")
print("=" * 50)

metrics_df.orderBy(
    col("f1_score").desc()
).show(truncate=False)


metrics_df.coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(metrics_path)

print("\nMetrics saved to:")
print(metrics_path)

print("\nSpark MLlib classification completed.")

spark.stop()
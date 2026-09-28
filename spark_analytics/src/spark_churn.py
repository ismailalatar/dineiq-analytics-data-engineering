from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.storagelevel import StorageLevel

from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.functions import vector_to_array

import os
import pandas as pd


# Start Spark

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("DineIQ_Spark_Churn")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)


# Project paths

CLEAN_DIR = r"D:\DineIQ\full_output\processed_data\clean"

ORDERS_PATH = os.path.join(CLEAN_DIR, "Orders.parquet")
ITEMS_PATH = os.path.join(CLEAN_DIR, "Order_Items.parquet")
MENU_PATH = os.path.join(CLEAN_DIR, "Menu_Items.parquet")

TEST_PATH = r"D:\DineIQ\dual_test_cases.parquet"

OUTPUT_PATH = (
    r"D:\DineIQ\python_analytics"
    r"\python_pipeline\external\spark_forecast_results.parquet"
)


# Churn features

FEATURES = [
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
    "weekend_ratio",
    "freq_recent_90d",
    "freq_trend",
    "avg_days_between_orders",
    "distinct_categories",
]


# Read source data
# Pandas is used for reading because of the Windows Spark issue.
# The feature work and model training are still done with Spark.

print("Reading source data...")

orders_pd = pd.read_parquet(ORDERS_PATH)
items_pd = pd.read_parquet(ITEMS_PATH)
menu_pd = pd.read_parquet(MENU_PATH)

orders = spark.createDataFrame(orders_pd)
items = spark.createDataFrame(items_pd)
menu = spark.createDataFrame(menu_pd)

del orders_pd
del items_pd
del menu_pd

orders = (
    orders
    .withColumn(
        "order_timestamp",
        F.to_timestamp("order_timestamp")
    )
    .filter(
        F.col("order_status") == "completed"
    )
)

items = (
    items
    .withColumn(
        "quantity",
        F.coalesce(
            F.col("quantity").cast("double"),
            F.lit(0.0)
        )
    )
    .withColumn(
        "line_total",
        F.coalesce(
            F.col("line_total").cast("double"),
            F.lit(0.0)
        )
)
)
print("Orders:", orders.count())
print("Order Items:", items.count())
print("Menu Items:", menu.count())


# Training dates

FEATURE_END = "2024-06-30"
LABEL_START = "2024-07-01"
LABEL_END = "2024-09-30"


print()
print("=" * 70)
print("BUILDING SPARK TRAIN COHORT")
print("=" * 70)


# Get orders from the feature period

o = orders.filter(
    F.col("order_timestamp")
    < F.to_timestamp(F.lit(FEATURE_END))
)

print("Feature-window orders:", o.count())


# Add time features

o = (
    o
    .withColumn(
        "hour",
        F.hour("order_timestamp")
    )
    .withColumn(
        "weekend",
        F.dayofweek("order_timestamp")
        .isin([1, 7])
        .cast("double")
    )
    .withColumn(
        "peak",
        (
            (F.hour("order_timestamp") >= 11)
            &
            (F.hour("order_timestamp") <= 21)
        ).cast("double")
    )
)


# Build basic RFM features

rfm = (
    o.groupBy("customer_id")
    .agg(
        F.max("order_timestamp").alias("last_order"),
        F.min("order_timestamp").alias("first_order"),
        F.countDistinct("order_id").alias("frequency"),
    )
)


# Calculate spending and different items

oi = (
    items
    .join(
        o.select("order_id", "customer_id"),
        on="order_id",
        how="inner"
    )
)

monetary = (
    oi.groupBy("customer_id")
    .agg(
        F.sum("line_total").alias("monetary"),
        F.countDistinct("menu_item_id").alias(
            "distinct_items"
        ),
    )
)


rfm = (
    rfm
    .join(
        monetary,
        on="customer_id",
        how="left"
    )
    .fillna(
        {
            "monetary": 0.0,
            "distinct_items": 0,
        }
    )
)


# Calculate recency and AOV

rfm = (
    rfm
    .withColumn(
        "recency",
        F.datediff(
            F.to_timestamp(F.lit(FEATURE_END)),
            F.col("last_order")
        )
    )
    .withColumn(
        "aov",
        F.round(
            F.col("monetary")
            /
            F.when(
                F.col("frequency") == 0,
                F.lit(1)
            )
            .otherwise(
                F.col("frequency")
            ),
            2
        )
    )
)


# Calculate RFM scores
# Use quartile values instead of a global ranking window.

def make_quartile_score(column_name, reverse=False):

    quantiles = (
        rfm
        .select(column_name)
        .where(
            F.col(column_name).isNotNull()
        )
        .approxQuantile(
            column_name,
            [0.25, 0.50, 0.75],
            0.01
        )
    )

    if len(quantiles) != 3:
        return F.lit(1)

    q1, q2, q3 = quantiles

    if reverse:
        return (
            F.when(
                F.col(column_name) <= q1,
                4
            )
            .when(
                F.col(column_name) <= q2,
                3
            )
            .when(
                F.col(column_name) <= q3,
                2
            )
            .otherwise(1)
        )

    return (
        F.when(
            F.col(column_name) <= q1,
            1
        )
        .when(
            F.col(column_name) <= q2,
            2
        )
        .when(
            F.col(column_name) <= q3,
            3
        )
        .otherwise(4)
    )


rfm = (
    rfm
    .withColumn(
        "r_score",
        make_quartile_score(
            "recency",
            reverse=True
        )
    )
    .withColumn(
        "f_score",
        make_quartile_score(
            "frequency",
            reverse=False
        )
    )
    .withColumn(
        "m_score",
        make_quartile_score(
            "monetary",
            reverse=False
        )
    )
)


# Customer behavior features

behavioral = (
    o.groupBy("customer_id")
    .agg(
        F.avg("peak").alias(
            "peak_ratio"
        ),

        F.avg("weekend").alias(
            "weekend_ratio"
        ),

        F.avg(
            F.when(
                F.col("promotion_id").isNotNull(),
                1.0
            )
            .otherwise(0.0)
        ).alias(
            "promo_sensitivity"
        ),
    )
)


# Count orders from the last 90 days

recent_start = F.date_sub(
    F.to_date(F.lit(FEATURE_END)),
    90
)

freq_90 = (
    o
    .filter(
        F.to_date("order_timestamp")
        >= recent_start
    )
    .groupBy("customer_id")
    .agg(
        F.countDistinct("order_id").alias(
            "freq_recent_90d"
        )
    )
)


freq_all = (
    o.groupBy("customer_id")
    .agg(
        F.countDistinct("order_id").alias(
            "total_freq"
        )
    )
)


freq_df = (
    freq_all
    .join(
        freq_90,
        on="customer_id",
        how="left"
    )
    .fillna(
        {
            "freq_recent_90d": 0
        }
    )
    .withColumn(
        "freq_trend",
        F.round(
            F.col("freq_recent_90d")
            /
            F.when(
                F.col("total_freq") == 0,
                F.lit(1)
            )
            .otherwise(
                F.col("total_freq")
            ),
            4
        )
    )
    .select(
        "customer_id",
        "freq_recent_90d",
        "freq_trend"
    )
)


# Calculate average days between orders

gap_window = (
    Window
    .partitionBy("customer_id")
    .orderBy("order_timestamp")
)

gaps = (
    o
    .withColumn(
        "_previous_order",
        F.lag("order_timestamp")
        .over(gap_window)
    )
    .withColumn(
        "_gap_days",
        F.datediff(
            "order_timestamp",
            "_previous_order"
        )
    )
    .groupBy("customer_id")
    .agg(
        F.coalesce(
            F.avg("_gap_days"),
            F.lit(0.0)
        ).alias(
            "avg_days_between_orders"
        )
    )
)


# Find distinct menu categories

oi_cat = (
    oi
    .join(
        menu.select(
            "menu_item_id",
            "category_id"
        ),
        on="menu_item_id",
        how="left"
    )
)

distinct_cat = (
    oi_cat
    .groupBy("customer_id")
    .agg(
        F.countDistinct(
            "category_id"
        ).alias(
            "distinct_categories"
        )
    )
)


# Combine customer features

train_features = (
    rfm.select(
        "customer_id",
        "recency",
        "frequency",
        "monetary",
        "aov",
        "distinct_items",
        "r_score",
        "f_score",
        "m_score",
    )
    .join(
        behavioral,
        "customer_id",
        "left"
    )
    .join(
        freq_df,
        "customer_id",
        "left"
    )
    .join(
        gaps,
        "customer_id",
        "left"
    )
    .join(
        distinct_cat,
        "customer_id",
        "left"
    )
    .fillna(
        {
            "peak_ratio": 0.0,
            "weekend_ratio": 0.0,
            "promo_sensitivity": 0.0,
            "freq_recent_90d": 0.0,
            "freq_trend": 0.0,
            "avg_days_between_orders": 0.0,
            "distinct_categories": 0.0,
        }
    )
)


# Create the churn label

active_customers = (
    orders
    .filter(
        (
            F.col("order_timestamp")
            >= F.to_timestamp(
                F.lit(LABEL_START)
            )
        )
        &
        (
            F.col("order_timestamp")
            <= F.to_timestamp(
                F.lit(LABEL_END)
            )
        )
    )
    .select("customer_id")
    .distinct()
    .withColumn(
        "bought_later",
        F.lit(1)
    )
)


train = (
    train_features
    .join(
        active_customers,
        "customer_id",
        "left"
    )
    .fillna(
        {
            "bought_later": 0
        }
    )
    .withColumn(
        "churn",
        (
            F.lit(1)
            -
            F.col("bought_later")
        ).cast("double")
    )
    .filter(
        F.col("frequency") > 0
    )
)


print(
    "Spark Train Cohort rows:",
    train.count()
)

print()
print("Spark Train Cohort schema:")

train.select(
    ["customer_id"] + FEATURES + ["churn"]
).printSchema()


# Prepare features for ML

assembler = VectorAssembler(
    inputCols=FEATURES,
    outputCol="features"
)

train_ready = assembler.transform(train)


# Calculate class weights
#
# Python original:
# class_weight="balanced"

class_counts = (
    train
    .groupBy("churn")
    .count()
    .collect()
)

count_by_class = {
    int(row["churn"]): row["count"]
    for row in class_counts
}

total = sum(
    count_by_class.values()
)

num_classes = len(
    count_by_class
)

weights = {
    cls:
        total /
        (
            num_classes *
            count
        )
    for cls, count in count_by_class.items()
}


print()
print("Class counts:", count_by_class)
print("Class weights:", weights)


train_ready = (
    train_ready
    .withColumn(
        "class_weight",
        F.when(
            F.col("churn") == 0,
            F.lit(
                float(
                    weights.get(0, 1.0)
                )
            )
        )
        .otherwise(
            F.lit(
                float(
                    weights.get(1, 1.0)
                )
            )
        )
    )
)


# Keep the training data in memory

train_ready = train_ready.persist(
    StorageLevel.MEMORY_AND_DISK
)

print()
print("Materializing training dataset...")

training_rows = train_ready.count()

print(
    "Materialized training rows:",
    training_rows
)


# Train the Spark Random Forest
#
# Python:
#   n_estimators=300
#   max_depth=12
#   min_samples_leaf=5
#   class_weight=balanced
#   random_state=42
#
# Spark:
#   numTrees=300
#   maxDepth=12
#   minInstancesPerNode=5
#   weightCol=class_weight
#   seed=42

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="churn",
    weightCol="class_weight",
    numTrees=300,
    maxDepth=12,
    minInstancesPerNode=5,
    seed=42
)


print()
print("=" * 70)
print("TRAINING SPARK RANDOM FOREST")
print("=" * 70)

model = rf.fit(train_ready)

print()
print("Spark training completed.")


# Read the 100 test cases

print()
print("Reading exact 100 dual test cases...")

test_pd = pd.read_parquet(TEST_PATH)

print(
    "Test rows:",
    len(test_pd)
)

test = spark.createDataFrame(
    test_pd
)

del test_pd


# Make predictions

test_ready = assembler.transform(test)

preds = model.transform(test_ready)


# Get positive class probability

preds = (
    preds
    .withColumn(
        "spark_probability",
        vector_to_array(
            F.col("probability")
        )[1].cast("double")
    )
)


result = preds.select(
    F.col("record_id"),
    F.col("customer_id"),
    F.col("churn"),
    F.col("prediction").alias(
        "spark_prediction"
    ),
    F.col("spark_probability")
)


# Convert results to Pandas and save
#
# Pandas and PyArrow are used here because of the
# Windows NativeIO issue.

print()
print(
    "Converting Spark predictions to Pandas..."
)

result_pd = result.toPandas()


if os.path.exists(OUTPUT_PATH):
    os.remove(OUTPUT_PATH)


print(
    "Saving Spark predictions..."
)

result_pd.to_parquet(
    OUTPUT_PATH,
    engine="pyarrow",
    index=False
)


# Show final results

print()
print("=" * 70)
print("SPARK CHURN COMPLETE")
print("=" * 70)

print(
    "Training rows:",
    training_rows
)

print(
    "Test rows:",
    len(result_pd)
)

print(
    "Output:",
    OUTPUT_PATH
)

print()
print("Prediction distribution:")

print(
    result_pd[
        "spark_prediction"
    ].value_counts().to_dict()
)

print()
print(
    result_pd
    .head(10)
    .to_string(index=False)
)


# Clean up

train_ready.unpersist()

spark.stop()

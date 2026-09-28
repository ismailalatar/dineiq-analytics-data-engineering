from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    lit,
    to_date,
    greatest,
)
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml import Pipeline
import os
import pandas as pd
import numpy as np


# ============================================================
# Project paths
# ============================================================

BASE_DIR = r"D:\DineIQ"

ORDERS_PATH = os.path.join(
    BASE_DIR,
    "full_output",
    "processed_data",
    "clean",
    "Orders.parquet"
)

ORDER_ITEMS_PATH = os.path.join(
    BASE_DIR,
    "full_output",
    "processed_data",
    "clean",
    "Order_Items.parquet"
)

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "spark_analytics",
    "results",
    "demand_forecast_spark.parquet"
)

MODEL_VERSION = "v2.0"


# ============================================================
# Start Spark
# ============================================================

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("DineIQ Item Demand Forecasting v2")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 60)
print("DINEIQ - ITEM LEVEL DEMAND FORECASTING v2.0")
print("=" * 60)


# ============================================================
# Read Parquet through Pandas
# Windows NativeIO workaround
# ============================================================

orders_pd = pd.read_parquet(ORDERS_PATH)
order_items_pd = pd.read_parquet(ORDER_ITEMS_PATH)

print("Orders rows:", len(orders_pd))
print("Order_Items rows:", len(order_items_pd))


# ============================================================
# Prepare valid completed order lines
# ============================================================

orders_pd["order_timestamp"] = pd.to_datetime(
    orders_pd["order_timestamp"]
)

valid_order_ids = set(
    orders_pd.loc[
        orders_pd["order_status"].astype(str).str.lower()
        == "completed",
        "order_id"
    ]
)

valid = order_items_pd[
    order_items_pd["order_id"].isin(valid_order_ids)
].copy()

valid = valid[
    (valid["quantity"] > 0)
    & (valid["unit_price"] > 0)
    & (valid["line_total"] >= 0)
].copy()

orders_lookup = orders_pd[
    ["order_id", "order_timestamp"]
]

valid = valid.merge(
    orders_lookup,
    on="order_id",
    how="inner"
)

valid["date"] = (
    valid["order_timestamp"]
    .dt.normalize()
)

print(
    "Valid revenue lines:",
    len(valid)
)


# ============================================================
# Daily revenue by menu item
# ============================================================

daily_sales = (
    valid
    .groupby(
        ["date", "menu_item_id"],
        as_index=False
    )["line_total"]
    .sum()
    .rename(
        columns={
            "line_total": "actual"
        }
    )
)

print(
    "Observed daily item rows:",
    len(daily_sales)
)

print(
    "Unique menu items:",
    daily_sales["menu_item_id"].nunique()
)


# ============================================================
# Create complete item-date calendar
#
# Missing item/date combinations represent zero observed
# revenue for that item on that date.
# ============================================================

start_date = daily_sales["date"].min()
end_date = daily_sales["date"].max()

items = (
    daily_sales["menu_item_id"]
    .drop_duplicates()
    .sort_values()
    .tolist()
)

dates = pd.date_range(
    start=start_date,
    end=end_date,
    freq="D"
)

calendar = pd.MultiIndex.from_product(
    [dates, items],
    names=["date", "menu_item_id"]
).to_frame(
    index=False
)

daily = calendar.merge(
    daily_sales,
    on=["date", "menu_item_id"],
    how="left"
)

daily["actual"] = (
    daily["actual"]
    .fillna(0.0)
    .astype(float)
)

daily = daily.sort_values(
    ["menu_item_id", "date"]
).reset_index(drop=True)

print(
    "Complete daily item rows:",
    len(daily)
)


# ============================================================
# Time-series features
#
# All lag/rolling features use only earlier observations.
# ============================================================

grouped = daily.groupby(
    "menu_item_id",
    group_keys=False
)

daily["lag_1"] = grouped["actual"].shift(1)

daily["lag_7"] = grouped["actual"].shift(7)

daily["rolling_7"] = grouped["actual"].transform(
    lambda s: s.shift(1).rolling(
        window=7,
        min_periods=1
    ).mean()
)

daily["rolling_14"] = grouped["actual"].transform(
    lambda s: s.shift(1).rolling(
        window=14,
        min_periods=1
    ).mean()
)

daily["day_of_week"] = (
    daily["date"].dt.dayofweek
)

daily["month"] = (
    daily["date"].dt.month
)

daily["time_index"] = (
    daily.groupby("menu_item_id").cumcount()
    + 1
)


# ============================================================
# Remove rows without enough history
# ============================================================

daily_model = daily.dropna(
    subset=[
        "lag_1",
        "lag_7",
        "rolling_7",
        "rolling_14"
    ]
).copy()


# ============================================================
# Chronological train/test split
#
# Last 20% of dates for each item are test data.
# No random split.
# ============================================================

daily_model["total_rows"] = (
    daily_model.groupby("menu_item_id")["date"]
    .transform("count")
)

daily_model["train_size"] = (
    daily_model["total_rows"] * 0.80
).astype(int)

daily_model["row_number"] = (
    daily_model.groupby("menu_item_id")
    .cumcount()
    + 1
)

train_pd = daily_model[
    daily_model["row_number"]
    <= daily_model["train_size"]
].copy()

test_pd = daily_model[
    daily_model["row_number"]
    > daily_model["train_size"]
].copy()

print("\nChronological split:")
print("Training rows:", len(train_pd))
print("Testing rows:", len(test_pd))

print(
    "Training date:",
    train_pd["date"].min().date(),
    "to",
    train_pd["date"].max().date()
)

print(
    "Testing date:",
    test_pd["date"].min().date(),
    "to",
    test_pd["date"].max().date()
)


# ============================================================
# Convert to Spark
# ============================================================

feature_columns = [
    "lag_1",
    "lag_7",
    "rolling_7",
    "rolling_14",
    "day_of_week",
    "month",
    "time_index",
]

train = spark.createDataFrame(
    train_pd[
        feature_columns + ["actual"]
    ]
)

test = spark.createDataFrame(
    test_pd[
        feature_columns
        + [
            "date",
            "menu_item_id",
            "actual",
        ]
    ]
)


# ============================================================
# Assemble features
# ============================================================

assembler = VectorAssembler(
    inputCols=feature_columns,
    outputCol="features"
)


# ============================================================
# Spark MLlib Random Forest Regressor
# ============================================================

regressor = RandomForestRegressor(
    featuresCol="features",
    labelCol="actual",
    predictionCol="predicted",
    numTrees=200,
    maxDepth=10,
    minInstancesPerNode=3,
    seed=42
)

pipeline = Pipeline(
    stages=[
        assembler,
        regressor
    ]
)


# ============================================================
# Train model
# ============================================================

print(
    "\nTraining Spark MLlib Random Forest forecasting model..."
)

model = pipeline.fit(train)


# ============================================================
# Generate predictions
# ============================================================

predictions = model.transform(test)


# ============================================================
# Prevent negative revenue predictions
# ============================================================

predictions = predictions.withColumn(
    "predicted",
    greatest(
        col("predicted").cast("double"),
        lit(0.0)
    )
)


# ============================================================
# Required final output
# ============================================================

forecast = (
    predictions
    .select(
        col("date"),
        col("menu_item_id").alias("item_id"),
        col("actual"),
        col("predicted"),
        lit(MODEL_VERSION).alias(
            "model_version"
        )
    )
    .orderBy(
        "date",
        "item_id"
    )
)


# ============================================================
# Show results
# ============================================================

print("\nForecast sample:")

forecast.show(
    20,
    truncate=False
)

forecast_count = forecast.count()

print(
    "Forecast rows:",
    forecast_count
)

print(
    "Forecast columns:",
    forecast.columns
)


# ============================================================
# Save through Pandas
# Windows Spark local Parquet workaround
# ============================================================

forecast_pd = forecast.toPandas()

# Remove old output if it exists as a file/directory
if os.path.exists(OUTPUT_PATH):

    if os.path.isdir(OUTPUT_PATH):
        import shutil

        shutil.rmtree(
            OUTPUT_PATH
        )
    else:
        os.remove(
            OUTPUT_PATH
        )

forecast_pd.to_parquet(
    OUTPUT_PATH,
    index=False
)

print("\nForecast saved to:")
print(OUTPUT_PATH)

print(
    "Saved rows:",
    len(forecast_pd)
)

print(
    "Saved columns:",
    forecast_pd.columns.tolist()
)


# ============================================================
# Stop Spark
# ============================================================

spark.stop()

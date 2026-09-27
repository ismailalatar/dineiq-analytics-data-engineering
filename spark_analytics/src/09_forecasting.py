from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, sum as spark_sum, count
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.ml import Pipeline
import os

# Project paths
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
    "student2",
    "results",
    "forecast_results.parquet"
)

# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Revenue Forecasting")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("DINEIQ - REVENUE FORECASTING")

# Read orders and order items
orders = spark.read.parquet(ORDERS_PATH)
order_items = spark.read.parquet(ORDER_ITEMS_PATH)

print("Orders rows:", orders.count())
print("Order_Items rows:", order_items.count())

# Keep valid completed revenue lines
valid_revenue_lines = (
    order_items
    .join(
        orders.select(
            "order_id",
            "order_timestamp",
            "order_status"
        ),
        on="order_id",
        how="inner"
    )
    .filter(
        (col("order_status") == "completed") &
        (col("quantity") > 0) &
        (col("unit_price") > 0) &
        (col("line_total") >= 0)
    )
)

print("Valid revenue lines:", valid_revenue_lines.count())

# Create daily revenue data
daily = (
    valid_revenue_lines
    .withColumn("date", to_date("order_timestamp"))
    .groupBy("date")
    .agg(
        spark_sum("line_total").alias("revenue"),
        count("*").alias("order_line_count")
    )
    .orderBy("date")
)

print("\nDaily data:")
print("Daily rows:", daily.count())
daily.show(10)

# Add a sequential time index
window = Window.orderBy("date")

daily = daily.withColumn(
    "time_index",
    row_number().over(window)
)

total_rows = daily.count()

# Set the size of the test data
test_size = max(
    30,
    int(total_rows * 0.20)
)

train_size = total_rows - test_size

# Split the data chronologically
train = daily.filter(
    col("time_index") <= train_size
)

test = daily.filter(
    col("time_index") > train_size
)

print("\nChronological split:")
print("Total rows:", total_rows)
print("Training rows:", train.count())
print("Testing rows:", test.count())

print("\nTraining sample:")

train.select(
    "date",
    "revenue"
).orderBy("date").show(5)

print("\nLast training dates:")

train.select(
    "date",
    "revenue"
).orderBy(
    col("date").desc()
).show(5)

print("\nFirst testing dates:")

test.select(
    "date",
    "revenue"
).orderBy("date").show(5)

# Prepare the feature vector
assembler = VectorAssembler(
    inputCols=["time_index"],
    outputCol="features"
)

# Create the linear regression model
regression = LinearRegression(
    featuresCol="features",
    labelCol="revenue",
    predictionCol="prediction"
)

# Build the forecasting pipeline
pipeline = Pipeline(
    stages=[
        assembler,
        regression
    ]
)

print("\nTraining forecasting model...")

model = pipeline.fit(train)

# Generate predictions for the test data
predictions = model.transform(test)

forecast = predictions.select(
    "date",
    "time_index",
    "revenue",
    "prediction",
    "order_line_count"
).orderBy("date")

print("\nForecast results:")
forecast.show(20, False)

print("Actual test rows:", test.count())
print("Forecast rows:", forecast.count())

# Save forecast results
forecast.write.mode("overwrite").parquet(OUTPUT_PATH)

print("\nForecast results saved to:")
print(OUTPUT_PATH)

print("\nRevenue forecasting completed successfully.")

spark.stop()
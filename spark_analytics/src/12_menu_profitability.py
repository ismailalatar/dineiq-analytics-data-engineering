from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, lit, coalesce, when

# Input and output paths
BASE = r"D:\DineIQ\full_output\processed_data"

FEATURES = BASE + r"\features\item_features.parquet"

ORDERS = BASE + r"\clean\Orders.parquet"

ORDER_ITEMS = BASE + r"\clean\Order_Items.parquet"

OUTPUT = r"D:\DineIQ\spark_analytics\results\menu_profitability.parquet"

# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Menu Profitability")
    .getOrCreate()
)

print("Loading item features...")

# Read item features
item = spark.read.parquet(FEATURES)

print("Loading orders...")

# Read order information
orders = (
    spark.read.parquet(ORDERS)
    .select("order_id", "order_timestamp")
)

print("Loading order items...")

# Read order item information
order_items = (
    spark.read.parquet(ORDER_ITEMS)
    .select("order_id", "menu_item_id", "quantity")
)

# Join orders with order items
order_items = order_items.join(
    orders,
    "order_id",
    "inner"
)

# Calculate sales for the first half of the year
h1 = (
    order_items
    .filter(col("order_timestamp") < lit("2024-07-01"))
    .groupBy("menu_item_id")
    .agg(
        sum("quantity").alias("h1_quantity")
    )
)

# Calculate sales for the second half of the year
h2 = (
    order_items
    .filter(col("order_timestamp") >= lit("2024-07-01"))
    .groupBy("menu_item_id")
    .agg(
        sum("quantity").alias("h2_quantity")
    )
)

# Combine the two periods
trend = h1.join(
    h2,
    "menu_item_id",
    "full"
)

# Replace missing values with zero
trend = trend.select(
    "menu_item_id",
    coalesce(col("h1_quantity"), lit(0)).alias("h1_quantity"),
    coalesce(col("h2_quantity"), lit(0)).alias("h2_quantity")
)

# Calculate the sales trend percentage
trend = trend.withColumn(
    "sales_trend_pct",
    when(
        col("h1_quantity") == 0,
        when(
            col("h2_quantity") > 0,
            lit(100.0)
        ).otherwise(lit(0.0))
    ).otherwise(
        (
            (col("h2_quantity") - col("h1_quantity"))
            / col("h1_quantity")
        ) * 100
    )
)

# Join the trend data with item features
result = item.join(
    trend,
    "menu_item_id",
    "left"
)

# Select the final columns
result = result.select(
    "menu_item_id",
    "item_name",
    "category_id",
    "category_name",
    "quantity_sold",
    "revenue",
    "cost",
    "contribution_margin",
    "profit_pct",
    "avg_rating",
    "repeat_purchase_rate",
    "wastage_pct",
    "promotion_dependency",
    "sales_trend_pct",
    "h1_quantity",
    "h2_quantity",
    "order_frequency",
    "distinct_customers",
    "rating_count",
    "total_wastage_cost",
    "discount_total",
    "min_price",
    "max_price"
)

print("Saving menu profitability dataset...")

# Save the result
result.write.mode("overwrite").parquet(OUTPUT)

print("STEP 9 COMPLETED")

print("Rows:", result.count())

print("Columns:", len(result.columns))

print("Sample:")

result.select(
    "menu_item_id",
    "item_name",
    "quantity_sold",
    "revenue",
    "cost",
    "contribution_margin",
    "profit_pct",
    "avg_rating",
    "repeat_purchase_rate",
    "wastage_pct",
    "promotion_dependency",
    "sales_trend_pct"
).show(15, truncate=False)

spark.stop()

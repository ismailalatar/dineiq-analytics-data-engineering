from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum, countDistinct, count, when, lit,
    max as spark_max,
    min as spark_min,
    month,
    dayofweek,
    datediff,
    min as spark_min_date,
    max as spark_max_date
)
from pyspark.sql.window import Window

# Input and output paths
BASE = r"D:\DineIQ\full_output\processed_data"

MENU = r"D:\DineIQ\spark_analytics\results\menu_profitability.parquet"

CLASSIFICATION = r"D:\DineIQ\spark_analytics\results\menu_performance_classification.parquet"

ORDERS = BASE + r"\clean\Orders.parquet"

ORDER_ITEMS = BASE + r"\clean\Order_Items.parquet"

OUTPUT = r"D:\DineIQ\spark_analytics\results\tricky_menu_cases_final.parquet"

# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Tricky Menu Cases")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("STEP 11 - TRICKY MENU PERFORMANCE CASES")

print("\nLoading menu data...")

# Load menu and classification data
menu = spark.read.parquet(MENU)

classification = spark.read.parquet(CLASSIFICATION).select(
    "menu_item_id",
    "performance_class"
)

# Add performance class to menu data
menu = menu.join(
    classification,
    "menu_item_id",
    "left"
)

print("Menu items:", menu.count())

print("\nCalculating thresholds...")

# Calculate median values for the menu indicators
sales_median = menu.approxQuantile(
    "quantity_sold", [0.50], 0.001
)[0]

margin_median = menu.approxQuantile(
    "contribution_margin", [0.50], 0.001
)[0]

rating_median = menu.approxQuantile(
    "avg_rating", [0.50], 0.001
)[0]

wastage_median = menu.approxQuantile(
    "wastage_pct", [0.50], 0.001
)[0]

promotion_median = menu.approxQuantile(
    "promotion_dependency", [0.50], 0.001
)[0]

print("Sales median:", sales_median)

print("Margin median:", margin_median)

print("Rating median:", rating_median)

print("Wastage median:", wastage_median)

print("Promotion median:", promotion_median)

print("\nLoading order data...")

# Load orders and order items
orders = spark.read.parquet(ORDERS)

order_items = spark.read.parquet(ORDER_ITEMS)

# Join order items with order information
oi = order_items.join(
    orders.select(
        "order_id",
        "order_timestamp",
        "restaurant_id",
        "order_status"
    ),
    "order_id",
    "inner"
)

print("\nCASE 1 - High-selling but loss-making")

# Find high-selling items with negative profit
case1 = (
    menu
    .filter(
        (col("quantity_sold") >= sales_median) &
        (col("contribution_margin") < 0)
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "contribution_margin",
        "profit_pct",
        lit("High-selling but loss-making").alias("case_type")
    )
)

print("CASE 2 - Highly profitable but rarely purchased")

# Find profitable items with low sales
case2 = (
    menu
    .filter(
        (col("contribution_margin") >= margin_median) &
        (col("quantity_sold") < sales_median)
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "contribution_margin",
        "profit_pct",
        lit("Highly profitable but rarely purchased").alias("case_type")
    )
)

print("CASE 3 - Popular with excessive wastage")

# Find popular items with high wastage
case3 = (
    menu
    .filter(
        (col("quantity_sold") >= sales_median) &
        (col("wastage_pct") > wastage_median)
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "wastage_pct",
        "total_wastage_cost",
        lit("Popular with excessive wastage").alias("case_type")
    )
)

print("CASE 4 - Highly rated with poor profitability")

# Find highly rated items with negative profit
case4 = (
    menu
    .filter(
        (col("avg_rating") >= rating_median) &
        (col("contribution_margin") < 0)
    )
    .select(
        "menu_item_id",
        "item_name",
        "avg_rating",
        "contribution_margin",
        "profit_pct",
        lit("Highly rated with poor profitability").alias("case_type")
    )
)

print("CASE 5 - Low-rated with high sales")

# Find low-rated items with high sales
case5 = (
    menu
    .filter(
        (col("avg_rating") < rating_median) &
        (col("quantity_sold") >= sales_median)
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "avg_rating",
        "revenue",
        lit("Low-rated with high sales").alias("case_type")
    )
)

print("CASE 6 - Promotion-dependent")

# Find items with high promotion dependency
case6 = (
    menu
    .filter(
        col("promotion_dependency") >= promotion_median
    )
    .select(
        "menu_item_id",
        "item_name",
        "promotion_dependency",
        "quantity_sold",
        "revenue",
        lit("Promotion-dependent").alias("case_type")
    )
)

print("CASE 7 - Different performance across locations")

# Calculate item sales for each restaurant
location_item = (
    oi
    .groupBy("restaurant_id", "menu_item_id")
    .agg(
        sum("quantity").alias("location_quantity"),
        countDistinct("order_id").alias("location_orders")
    )
)

# Find differences in item performance between locations
location_stats = (
    location_item
    .groupBy("menu_item_id")
    .agg(
        spark_max("location_quantity").alias("max_location_quantity"),
        spark_min("location_quantity").alias("min_location_quantity"),
        countDistinct("restaurant_id").alias("location_count")
    )
)

case7 = (
    location_stats
    .filter(
        (col("location_count") >= 2) &
        (col("max_location_quantity") >
         col("min_location_quantity") * 2)
    )
    .join(
        menu.select(
            "menu_item_id",
            "item_name",
            "quantity_sold",
            "revenue",
            "contribution_margin"
        ),
        "menu_item_id",
        "left"
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "revenue",
        "contribution_margin",
        "max_location_quantity",
        "min_location_quantity",
        "location_count",
        lit("Different performance across locations").alias("case_type")
    )
)

print("CASE 8 - Weekend-only strong performance")

# Separate weekday and weekend sales
weekend_data = (
    oi
    .withColumn(
        "is_weekend",
        when(
            dayofweek("order_timestamp").isin([1, 7]),
            1
        ).otherwise(0)
    )
    .groupBy("menu_item_id", "is_weekend")
    .agg(
        sum("quantity").alias("quantity")
    )
)

# Compare weekday and weekend quantities
weekend_pivot = (
    weekend_data
    .groupBy("menu_item_id")
    .pivot("is_weekend", [0, 1])
    .sum("quantity")
    .fillna(0)
    .withColumnRenamed("0", "weekday_quantity")
    .withColumnRenamed("1", "weekend_quantity")
)

case8 = (
    weekend_pivot
    .filter(
        (col("weekend_quantity") > col("weekday_quantity")) &
        (col("weekend_quantity") >= col("weekday_quantity") * 1.5)
    )
    .join(
        menu.select(
            "menu_item_id",
            "item_name",
            "quantity_sold",
            "revenue"
        ),
        "menu_item_id",
        "left"
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "revenue",
        "weekday_quantity",
        "weekend_quantity",
        lit("Performs well only on weekends").alias("case_type")
    )
)

print("CASE 9 - Seasonal menu item")

# Calculate monthly sales for each item
monthly_data = (
    oi
    .withColumn(
        "month_num",
        month("order_timestamp")
    )
    .groupBy("menu_item_id", "month_num")
    .agg(
        sum("quantity").alias("monthly_quantity")
    )
)

# Find the highest and lowest monthly sales
seasonal_stats = (
    monthly_data
    .groupBy("menu_item_id")
    .agg(
        spark_max("monthly_quantity").alias("max_month_quantity"),
        spark_min("monthly_quantity").alias("min_month_quantity"),
        countDistinct("month_num").alias("active_months")
    )
)

case9 = (
    seasonal_stats
    .filter(
        (col("active_months") >= 6) &
        (col("max_month_quantity") >
         col("min_month_quantity") * 2)
    )
    .join(
        menu.select(
            "menu_item_id",
            "item_name",
            "quantity_sold",
            "revenue"
        ),
        "menu_item_id",
        "left"
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "revenue",
        "max_month_quantity",
        "min_month_quantity",
        "active_months",
        lit("Seasonal menu item").alias("case_type")
    )
)

print("CASE 10 - New menu item with insufficient history")

# Find the first and last order date for each item
item_history = (
    oi
    .groupBy("menu_item_id")
    .agg(
        spark_min_date("order_timestamp").alias("first_order_date"),
        spark_max_date("order_timestamp").alias("last_order_date")
    )
)

# Get the last date in the dataset
data_end_date = orders.select(
    spark_max("order_timestamp").alias("data_end")
).collect()[0]["data_end"]

case10 = (
    item_history
    .withColumn(
        "history_days",
        datediff(
            lit(data_end_date),
            col("first_order_date")
        )
    )
    .filter(
        col("history_days") < 90
    )
    .join(
        menu.select(
            "menu_item_id",
            "item_name",
            "quantity_sold",
            "revenue",
            "contribution_margin"
        ),
        "menu_item_id",
        "left"
    )
    .select(
        "menu_item_id",
        "item_name",
        "quantity_sold",
        "revenue",
        "contribution_margin",
        "first_order_date",
        "last_order_date",
        "history_days",
        lit("New menu item with insufficient history").alias("case_type")
    )
)

print("\nCombining all cases...")

# Columns used in the final output
columns = [
    "menu_item_id",
    "item_name",
    "quantity_sold",
    "revenue",
    "contribution_margin",
    "profit_pct",
    "avg_rating",
    "wastage_pct",
    "total_wastage_cost",
    "promotion_dependency",
    "max_location_quantity",
    "min_location_quantity",
    "location_count",
    "weekday_quantity",
    "weekend_quantity",
    "max_month_quantity",
    "min_month_quantity",
    "active_months",
    "first_order_date",
    "last_order_date",
    "history_days",
    "case_type"
]

# Add missing columns before combining the cases
def standardize(df):
    for c in columns:
        if c not in df.columns:
            df = df.withColumn(c, lit(None))
    return df.select(*columns)

# Prepare all case results
cases = [
    standardize(case1),
    standardize(case2),
    standardize(case3),
    standardize(case4),
    standardize(case5),
    standardize(case6),
    standardize(case7),
    standardize(case8),
    standardize(case9),
    standardize(case10)
]

# Combine all cases
final_cases = cases[0]

for case in cases[1:]:
    final_cases = final_cases.unionByName(case)

# Save the final tricky cases
final_cases.write.mode("overwrite").parquet(OUTPUT)

print("\nTricky Case Summary:")

# Count records for each case type
summary = (
    final_cases
    .groupBy("case_type")
    .count()
    .orderBy("case_type")
)

summary.show(20, truncate=False)

total_cases = final_cases.count()

print("Total case records:", total_cases)

print("Output:", OUTPUT)

# Check the number of case types
distinct_case_types = (
    final_cases
    .select("case_type")
    .distinct()
    .count()
)

print("Distinct tricky case types:", distinct_case_types)

if distinct_case_types == 10:
    print("\nSTEP 11 COMPLETED SUCCESSFULLY")
else:
    print("\nSTEP 11 COMPLETED WITH WARNING")
    print("Some case types have zero matching records.")

spark.stop()

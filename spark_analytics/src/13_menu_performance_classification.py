from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when, percent_rank
from pyspark.sql.window import Window


INPUT = r"D:\DineIQ\student2\results\menu_profitability.parquet"
OUTPUT = r"D:\DineIQ\student2\results\menu_performance_classification.parquet"

spark = (
    SparkSession.builder
    .appName("DineIQ Menu Performance Classification")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("STEP 10 - MENU PERFORMANCE CLASSIFICATION")

print("\nLoading menu profitability dataset...")

df = spark.read.parquet(INPUT)

print("Input rows:", df.count())

print("\nCalculating sales indicators...")

quantity_window = Window.orderBy(col("quantity_sold"))
revenue_window = Window.orderBy(col("revenue"))
frequency_window = Window.orderBy(col("order_frequency"))
trend_window = Window.orderBy(col("sales_trend_pct"))

df = (
    df
    .withColumn(
        "quantity_score",
        percent_rank().over(quantity_window)
    )
    .withColumn(
        "revenue_score",
        percent_rank().over(revenue_window)
    )
    .withColumn(
        "frequency_score",
        percent_rank().over(frequency_window)
    )
    .withColumn(
        "trend_score",
        percent_rank().over(trend_window)
    )
)

df = df.withColumn(
    "sales_index",
    (
        col("quantity_score")
        + col("revenue_score")
        + col("frequency_score")
        + col("trend_score")
    ) / 4
)

print("Calculating profitability indicators...")

margin_window = Window.orderBy(col("contribution_margin"))
profit_pct_window = Window.orderBy(col("profit_pct"))
rating_window = Window.orderBy(col("avg_rating"))
repeat_window = Window.orderBy(col("repeat_purchase_rate"))
wastage_window = Window.orderBy(col("wastage_pct"))
promotion_window = Window.orderBy(col("promotion_dependency"))

df = (
    df
    .withColumn(
        "margin_score",
        percent_rank().over(margin_window)
    )
    .withColumn(
        "profit_pct_score",
        percent_rank().over(profit_pct_window)
    )
    .withColumn(
        "rating_score",
        percent_rank().over(rating_window)
    )
    .withColumn(
        "repeat_score",
        percent_rank().over(repeat_window)
    )
    .withColumn(
        "wastage_score",
        1 - percent_rank().over(wastage_window)
    )
    .withColumn(
        "promotion_score",
        1 - percent_rank().over(promotion_window)
    )
)

df = df.withColumn(
    "profitability_index",
    (
        col("margin_score")
        + col("profit_pct_score")
        + col("rating_score")
        + col("repeat_score")
        + col("wastage_score")
        + col("promotion_score")
    ) / 6
)

print("\nCalculating thresholds...")

sales_median = df.approxQuantile(
    "sales_index",
    [0.50],
    0.001
)[0]

profitability_median = df.approxQuantile(
    "profitability_index",
    [0.50],
    0.001
)[0]

print("Sales Index Median:", sales_median)
print("Profitability Index Median:", profitability_median)

df = (
    df
    .withColumn(
        "sales_level",
        when(
            col("sales_index") >= lit(sales_median),
            "High"
        ).otherwise("Low")
    )
    .withColumn(
        "profitability_level",
        when(
            col("profitability_index") >= lit(profitability_median),
            "High"
        ).otherwise("Low")
    )
)

df = df.withColumn(
    "performance_class",
    when(
        (col("sales_level") == "High") &
        (col("profitability_level") == "High"),
        "Profit Driver"
    )
    .when(
        (col("sales_level") == "High") &
        (col("profitability_level") == "Low"),
        "Volume Driver"
    )
    .when(
        (col("sales_level") == "Low") &
        (col("profitability_level") == "High"),
        "Hidden Opportunity"
    )
    .otherwise("Low Performer")
)

final_df = df.select(
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
    "sales_index",
    "profitability_index",
    "sales_level",
    "profitability_level",
    "performance_class"
)

print("\nSaving classification dataset...")

final_df.write.mode("overwrite").parquet(OUTPUT)

print("\nClassification Summary:")

summary = (
    final_df
    .groupBy("performance_class")
    .count()
    .orderBy("performance_class")
)

summary.show(truncate=False)

print("\nSample classified menu items:")

final_df.select(
    "menu_item_id",
    "item_name",
    "quantity_sold",
    "contribution_margin",
    "profit_pct",
    "avg_rating",
    "repeat_purchase_rate",
    "wastage_pct",
    "promotion_dependency",
    "sales_trend_pct",
    "sales_index",
    "profitability_index",
    "performance_class"
).orderBy(
    col("performance_class"),
    col("profitability_index").desc()
).show(20, truncate=False)

print("\nValidation:")

total_rows = final_df.count()

classified_rows = (
    final_df
    .filter(col("performance_class").isNotNull())
    .count()
)

distinct_classes = (
    final_df
    .select("performance_class")
    .distinct()
    .count()
)

print("Total menu items:", total_rows)
print("Classified menu items:", classified_rows)
print("Distinct classes:", distinct_classes)

if total_rows == classified_rows and distinct_classes == 4:
    print("\nSTEP 10 COMPLETED SUCCESSFULLY")
else:
    print("\nSTEP 10 VALIDATION FAILED")

spark.stop()
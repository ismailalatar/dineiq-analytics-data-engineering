from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, expr, desc


# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Menu Classification")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Input and output paths
input_path = r"D:\DineIQ\full_output\processed_data\features\item_features.parquet"
output_path = r"D:\DineIQ\spark_analytics\results\menu_classification.parquet"

df = spark.read.parquet(input_path)

print("\n===== MENU CLASSIFICATION =====")
print("Total menu items:", df.count())


# Calculate median values for sales and profit
medians = df.select(
    expr("percentile_approx(quantity_sold, 0.5)").alias("sales_median"),
    expr("percentile_approx(contribution_margin, 0.5)").alias("margin_median")
).collect()[0]

sales_median = medians["sales_median"]
margin_median = medians["margin_median"]

print("Sales median:", sales_median)
print("Contribution margin median:", margin_median)


# Assign sales, profit, and menu categories
classified = (
    df
    .withColumn(
        "sales_level",
        when(col("quantity_sold") >= sales_median, "High Sales")
        .otherwise("Low Sales")
    )
    .withColumn(
        "profit_level",
        when(col("contribution_margin") >= margin_median, "High Profit")
        .otherwise("Low Profit")
    )
    .withColumn(
        "menu_class",
        when(
            (col("quantity_sold") >= sales_median) &
            (col("contribution_margin") >= margin_median),
            "Star"
        )
        .when(
            (col("quantity_sold") >= sales_median) &
            (col("contribution_margin") < margin_median),
            "High Sales / Low Profit"
        )
        .when(
            (col("quantity_sold") < sales_median) &
            (col("contribution_margin") >= margin_median),
            "Low Sales / High Profit"
        )
        .otherwise("Low Sales / Low Profit")
    )
)


print("\n===== CLASSIFICATION COUNTS =====")

# Count items in each class
classified.groupBy("menu_class") \
    .count() \
    .orderBy("menu_class") \
    .show(truncate=False)


classes = [
    "Star",
    "High Sales / Low Profit",
    "Low Sales / High Profit",
    "Low Sales / Low Profit"
]

for menu_class in classes:

    print(f"\n===== {menu_class} =====")

    # Show a few items from each class
    classified.filter(
        col("menu_class") == menu_class
    ).select(
        "menu_item_id",
        "item_name",
        "category_name",
        "quantity_sold",
        "revenue",
        "contribution_margin",
        "profit_pct",
        "menu_class"
    ).orderBy(
        desc("quantity_sold")
    ).show(5, truncate=False)


# Save the classification results
classified.write \
    .mode("overwrite") \
    .parquet(output_path)

print("\nClassification results saved to:")
print(output_path)
print("\nMenu classification completed.")

spark.stop()

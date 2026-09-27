from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc, lit

# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Tricky Menu Cases")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# Set input and output paths
input_path = r"D:\DineIQ\full_output\processed_data\features\item_features.parquet"
output_path = r"D:\DineIQ\student2\results\tricky_menu_cases.parquet"

df = spark.read.parquet(input_path)

print("\nDINEIQ - TRICKY MENU CASES")
print("=" * 50)

print("Total menu items:", df.count())

# Calculate median values
sales_median = df.selectExpr(
    "percentile_approx(quantity_sold, 0.5) as median"
).collect()[0]["median"]

margin_median = df.selectExpr(
    "percentile_approx(contribution_margin, 0.5) as median"
).collect()[0]["median"]

wastage_median = df.selectExpr(
    "percentile_approx(wastage_pct, 0.5) as median"
).collect()[0]["median"]

rating_median = df.selectExpr(
    "percentile_approx(avg_rating, 0.5) as median"
).collect()[0]["median"]

promotion_median = df.selectExpr(
    "percentile_approx(promotion_dependency, 0.5) as median"
).collect()[0]["median"]

print("\nData-based thresholds")
print("Sales median:", sales_median)
print("Contribution margin:", margin_median)
print("Wastage median:", wastage_median)
print("Rating median:", rating_median)
print("Promotion dependency median:", promotion_median)

# Case 1: High sales but negative profit
print("\n1. High-selling but loss-making")

case1 = df.filter(
    (col("quantity_sold") >= sales_median) &
    (col("contribution_margin") < 0)
)

case1.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "quantity_sold",
    "revenue",
    "contribution_margin",
    "profit_pct"
).orderBy(desc("quantity_sold")).show(20, truncate=False)

print("Count:", case1.count())

# Case 2: Low sales but positive profit
print("\n2. Profitable but low-selling")

case2 = df.filter(
    (col("quantity_sold") < sales_median) &
    (col("contribution_margin") > 0)
)

case2.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "quantity_sold",
    "revenue",
    "contribution_margin",
    "profit_pct"
).orderBy(desc("contribution_margin")).show(20, truncate=False)

print("Count:", case2.count())

# Case 3: Popular items with high wastage
print("\n3. Popular + high wastage")

case3 = df.filter(
    (col("quantity_sold") >= sales_median) &
    (col("wastage_pct") >= wastage_median)
)

case3.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "quantity_sold",
    "wastage_pct",
    "total_wasted",
    "total_wastage_cost",
    "contribution_margin"
).orderBy(desc("wastage_pct")).show(20, truncate=False)

print("Count:", case3.count())

# Case 4: High rating but negative profit
print("\n4. Highly rated + poor profitability")

case4 = df.filter(
    (col("avg_rating") >= rating_median) &
    (col("contribution_margin") < 0)
)

case4.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "avg_rating",
    "rating_count",
    "quantity_sold",
    "revenue",
    "contribution_margin",
    "profit_pct"
).orderBy(desc("avg_rating")).show(20, truncate=False)

print("Count:", case4.count())

# Case 5: Low rating but high sales
print("\n5. Low-rated + high sales")

case5 = df.filter(
    (col("avg_rating") < rating_median) &
    (col("quantity_sold") >= sales_median)
)

case5.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "avg_rating",
    "rating_count",
    "quantity_sold",
    "revenue",
    "contribution_margin"
).orderBy(desc("quantity_sold")).show(20, truncate=False)

print("Count:", case5.count())

# Case 6: Items with high promotion dependency
print("\n6. Promotion-dependent items")

case6 = df.filter(
    col("promotion_dependency") >= promotion_median
)

case6.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "quantity_sold",
    "promotion_dependency",
    "qty_promoted",
    "revenue",
    "contribution_margin",
    "profit_pct"
).orderBy(
    desc("promotion_dependency")
).show(20, truncate=False)

print("Count:", case6.count())

# Columns used in the final output
base_columns = [
    "menu_item_id",
    "item_name",
    "category_name",
    "quantity_sold",
    "revenue",
    "contribution_margin",
    "profit_pct",
    "wastage_pct",
    "total_wasted",
    "total_wastage_cost",
    "avg_rating",
    "rating_count",
    "promotion_dependency",
    "qty_promoted"
]

# Add case type to each result
case1_output = case1.select(*base_columns).withColumn(
    "case_type", lit("High-selling but loss-making")
)

case2_output = case2.select(*base_columns).withColumn(
    "case_type", lit("Profitable but low-selling")
)

case3_output = case3.select(*base_columns).withColumn(
    "case_type", lit("Popular + high wastage")
)

case4_output = case4.select(*base_columns).withColumn(
    "case_type", lit("Highly rated + poor profitability")
)

case5_output = case5.select(*base_columns).withColumn(
    "case_type", lit("Low-rated + high sales")
)

case6_output = case6.select(*base_columns).withColumn(
    "case_type", lit("Promotion-dependent")
)

# Combine all cases
all_cases = (
    case1_output
    .unionByName(case2_output)
    .unionByName(case3_output)
    .unionByName(case4_output)
    .unionByName(case5_output)
    .unionByName(case6_output)
)

print("\nCase summary")

# Count each case type
all_cases.groupBy("case_type") \
    .count() \
    .orderBy("case_type") \
    .show(truncate=False)

print("Total case records:", all_cases.count())

# Save the results
all_cases.write \
    .mode("overwrite") \
    .parquet(output_path)

print("\nResult saved to:")
print(output_path)

print("\nTricky menu cases analysis completed.")

spark.stop()
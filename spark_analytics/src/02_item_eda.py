from pyspark.sql import SparkSession
from pyspark.sql.functions import desc, asc


spark = (
    SparkSession.builder
    .appName("DineIQ Item EDA")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


path = r"D:\DineIQ\full_output\processed_data\features\item_features.parquet"

df = spark.read.parquet(path)

print("\nDineIQ - Item EDA")
print("=" * 50)
print("Total menu items:", df.count())


print("\nTop 10 items by quantity sold")
print("=" * 50)

df.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "quantity_sold",
    "revenue",
    "contribution_margin"
).orderBy(desc("quantity_sold")).show(10, truncate=False)


print("\nTop 10 items by revenue")
print("=" * 50)

df.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "revenue",
    "quantity_sold",
    "contribution_margin"
).orderBy(desc("revenue")).show(10, truncate=False)


print("\nTop 10 items by contribution margin")
print("=" * 50)

df.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "contribution_margin",
    "revenue",
    "profit_pct"
).orderBy(desc("contribution_margin")).show(10, truncate=False)


print("\nBottom 10 items by contribution margin")
print("=" * 50)

df.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "contribution_margin",
    "revenue",
    "profit_pct"
).orderBy(asc("contribution_margin")).show(10, truncate=False)


print("\nTop 10 items by wastage %")
print("=" * 50)

df.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "wastage_pct",
    "total_wasted",
    "total_wastage_cost",
    "quantity_sold"
).orderBy(desc("wastage_pct")).show(10, truncate=False)


print("\nTop 10 items by rating")
print("=" * 50)

df.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "avg_rating",
    "rating_count",
    "quantity_sold",
    "profit_pct"
).orderBy(desc("avg_rating")).show(10, truncate=False)


print("\nTop 10 promotion-dependent items")
print("=" * 50)

df.select(
    "menu_item_id",
    "item_name",
    "category_name",
    "promotion_dependency",
    "qty_promoted",
    "quantity_sold",
    "profit_pct"
).orderBy(desc("promotion_dependency")).show(10, truncate=False)


print("\nEDA completed successfully.")

spark.stop()


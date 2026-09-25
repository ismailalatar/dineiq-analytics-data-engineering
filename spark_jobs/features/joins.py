from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col


ROOT = Path("D:/APTECH")
CLEAN = ROOT / "full_output" / "processed_data" / "clean"


def load_clean(spark: SparkSession, name: str):
    return spark.read.parquet(str(CLEAN / f"{name}.parquet"))


def build_integrated_fact(spark: SparkSession):
    """Implements all 10 required joins from SRS Step 6.

    Joins (from SRS Step 6):
      1. Orders with Customers
      2. Orders with Order_Items
      3. Order_Items with Menu_Items
      4. Menu_Items with Menu_Categories
      5. Orders with Restaurants
      6. Orders with Promotions
      7. Menu_Items with Pricing_History (effective at order time)
      8. Menu_Items with Ratings  (aggregate to item level)
      9. Menu_Items with Inventory (aggregate to item + restaurant)
     10. Menu_Items with Wastage (aggregate to item)
    """
    orders = load_clean(spark, "Orders")
    lines = load_clean(spark, "Order_Items")
    customers = load_clean(spark, "Customers")
    restaurants = load_clean(spark, "Restaurants")
    menu = load_clean(spark, "Menu_Items")
    cats = load_clean(spark, "Menu_Categories")
    pricing = load_clean(spark, "Pricing_History")
    promos = load_clean(spark, "Promotions")
    promo_items = load_clean(spark, "Promotion_Items")
    ratings = load_clean(spark, "Ratings")
    inventory = load_clean(spark, "Inventory")
    wastage = load_clean(spark, "Wastage")

    # Joins 1, 2, 5, 6 (Orders with Customers / Restaurants / Promotions)
    fact = (
        lines
        .join(orders, on="order_id", how="inner")                         # 2
        .join(customers, on="customer_id", how="left")                    # 1
        .join(restaurants, on="restaurant_id", how="left")                # 5
        .join(promos.select("promotion_id", "promotion_name", "discount_type", "discount_value"),
              on="promotion_id", how="left")                              # 6
    )

    # Join 3 (Order_Items with Menu_Items)
    fact = fact.join(
        menu.select("menu_item_id", "category_id", "item_name",
                    "base_price", "standard_cost", "unit_of_measure", "availability"),
        on="menu_item_id", how="left",
    )

    # Join 4 (Menu_Items with Menu_Categories)
    fact = fact.join(
        cats.select(col("category_id"), col("category_name")),
        on="category_id", how="left",
    )

    # Join 7 (Menu_Items with Pricing_History)
    # Aggregate: the count of distinct prices per item + latest price
    from pyspark.sql.functions import max as spark_max, min as spark_min

    pricing_agg = pricing.groupBy("menu_item_id").agg(
        spark_max("unit_price").alias("max_historical_price"),
        spark_min("unit_price").alias("min_historical_price"),
    )
    fact = fact.join(pricing_agg, on="menu_item_id", how="left")

    # Join 8 (Menu_Items with Ratings) — aggregate to item level
    from pyspark.sql.functions import avg as spark_avg, count as spark_count

    ratings_agg = ratings.groupBy("menu_item_id").agg(
        spark_avg("rating_value").alias("avg_rating"),
        spark_count("rating_id").alias("rating_count"),
    )
    fact = fact.join(ratings_agg, on="menu_item_id", how="left")

    # Join 9 (Menu_Items with Inventory) — aggregate to item level
    from pyspark.sql.functions import sum as spark_sum

    inventory_agg = inventory.groupBy("menu_item_id").agg(
        spark_sum("consumption_quantity").alias("total_consumption"),
        spark_sum("closing_quantity").alias("total_closing"),
    )
    fact = fact.join(inventory_agg, on="menu_item_id", how="left")

    # Join 10 (Menu_Items with Wastage) — aggregate to item level
    wastage_agg = wastage.groupBy("menu_item_id").agg(
        spark_sum("quantity_wasted").alias("total_wasted_quantity"),
        spark_sum("wastage_cost").alias("total_wastage_cost"),
    )
    fact = fact.join(wastage_agg, on="menu_item_id", how="left")

    return fact
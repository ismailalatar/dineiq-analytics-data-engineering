from __future__ import annotations

import json
import time
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, count, countDistinct, sum as spark_sum, max as spark_max,
    min as spark_min, when, lit, datediff, to_date, dayofweek, hour, month,
    coalesce, concat, lpad, first,least,
)

from .joins import build_integrated_fact, load_clean


ROOT = Path("D:/APTECH")
FEATURES = ROOT / "full_output" / "processed_data" / "features"
REPORTS = ROOT / "full_output" / "reports"


# ============================================================
# Item features (per menu_item_id)
# ============================================================

def build_item_features(fact, spark):
    f = fact
    f = f.withColumn("gross", col("quantity").cast("double") * col("unit_price").cast("double"))
    f = f.withColumn("line_cost", col("quantity").cast("double") * col("unit_cost").cast("double"))
    f = f.withColumn("line_cm", col("line_total").cast("double") - col("line_cost"))

    # Per-item aggregates
    base = f.groupBy("menu_item_id", "item_name", "category_id", "category_name").agg(
        spark_sum("quantity").cast("double").alias("quantity_sold"),
        spark_sum("gross").alias("revenue"),
        spark_sum("line_cost").alias("cost"),
        spark_sum("line_cm").alias("contribution_margin"),
        countDistinct("order_id").alias("order_frequency"),
        countDistinct("customer_id").alias("distinct_customers"),
        count("order_item_id").alias("line_count"),
        avg("avg_rating").alias("avg_rating"),
        spark_max("rating_count").alias("rating_count"),
        spark_sum("total_consumption").alias("total_consumption"),
        spark_sum("total_wasted_quantity").alias("total_wasted"),
        spark_sum("total_wastage_cost").alias("total_wastage_cost"),
        spark_sum("discount_amount").cast("double").alias("discount_total"),
        spark_max("max_historical_price").alias("max_price"),
        spark_min("min_historical_price").alias("min_price"),
        # Promotion dependency: quantity sold with promotion / total quantity
        spark_sum(when(col("promotion_id").isNotNull(), col("quantity")).otherwise(lit(0))).alias("qty_promoted"),
    )

    # Repeat-purchase rate per item:
    #   distinct customers with >= 2 orders containing this item / total distinct customers
    cust_repeat = (
        f.groupBy("menu_item_id", "customer_id")
         .agg(countDistinct("order_id").alias("cust_orders"))
         .filter(col("cust_orders") >= 2)
         .groupBy("menu_item_id")
         .agg(count("customer_id").alias("repeat_customers"))
    )

    # Rating trend: recent-half average minus early-half average
    # Uses raw Ratings so trend is not flattened to one item value.
    ratings = load_clean(spark, "Ratings")
    ratings = ratings.filter(
        col("menu_item_id").isNotNull() &
        col("rating_value").between(1, 5) &
        col("rating_timestamp").isNotNull()
    )
    ratings = ratings.withColumn("month_num", month("rating_timestamp"))
    monthly_r = ratings.groupBy("menu_item_id", "month_num").agg(avg("rating_value").alias("m_avg"))
    early_r = monthly_r.filter(col("month_num") <= 6).groupBy("menu_item_id").agg(avg("m_avg").alias("early_rating"))
    recent_r = monthly_r.filter(col("month_num") > 6).groupBy("menu_item_id").agg(avg("m_avg").alias("recent_rating"))
    rating_trend_df = early_r.join(recent_r, on="menu_item_id", how="full_outer")

    item = (
        base
        .join(cust_repeat, on="menu_item_id", how="left")
        .join(rating_trend_df, on="menu_item_id", how="left")
        .fillna({"repeat_customers": 0})
    )

    # SRS Step 7 derived features
    total_orders = f.select("order_id").distinct().count()

    item = (
        item
        .withColumn("profit_pct",
                    when(col("revenue") > 0, col("contribution_margin") / col("revenue")).otherwise(lit(0.0)))
        .withColumn("wastage_pct",
                    when(col("total_consumption") > 0, col("total_wasted") / col("total_consumption")).otherwise(lit(0.0)))
        .withColumn("discount_pct",
                    when(col("revenue") + col("discount_total") > 0,
                         col("discount_total") / (col("revenue") + col("discount_total"))).otherwise(lit(0.0)))
        .withColumn("discount_pct",
                    when(col("discount_pct") < 0.0, lit(0.0))
                    .when(col("discount_pct") > 1.0, lit(1.0))
                    .otherwise(col("discount_pct")))
        .withColumn("price_change_pct",
                    when((col("min_price").isNotNull()) & (col("min_price") > 0),
                         (col("max_price") - col("min_price")) / col("min_price")).otherwise(lit(0.0)))
        .withColumn("promotion_dependency",
                    when(col("quantity_sold") > 0,
                         col("qty_promoted").cast("double") / col("quantity_sold").cast("double")).otherwise(lit(0.0)))
        .withColumn("repeat_purchase_rate",
                    when(col("distinct_customers") > 0,
                         col("repeat_customers").cast("double") / col("distinct_customers").cast("double")).otherwise(lit(0.0)))
        .withColumn("basket_inclusion_rate",
                    when(lit(float(total_orders)) > 0,
                         col("order_frequency").cast("double") / lit(float(total_orders))).otherwise(lit(0.0)))
        .withColumn("rating_trend",
                    when(col("recent_rating").isNotNull() & col("early_rating").isNotNull(),
                         col("recent_rating") - col("early_rating")).otherwise(lit(0.0)))
    )

    return item


# ============================================================
# Customer features (per customer_id)
# ============================================================

def build_customer_features(fact, customers):
    """Customer-level features for EVERY registered customer (LEFT JOIN).

    Customers without valid orders receive zeros for monetary values and
    recency measured from registration. Required for churn analysis (SRS Step 36).
    """
    # Basic aggregates
    agg = fact.groupBy("customer_id").agg(
        spark_max("order_timestamp").alias("last_order_ts"),
        spark_min("order_timestamp").alias("first_order_ts"),
        countDistinct("order_id").alias("order_count"),
        spark_sum("line_total").cast("double").alias("monetary"),
        count("order_item_id").alias("line_count"),
        # Peak hour share: fraction of their orders in peak hours (11-21)
        countDistinct(when(hour("order_timestamp").between(11, 21), col("order_id"))).alias("peak_orders"),
        # Weekend share: fraction of their orders on Fri/Sat/Sun
        countDistinct(when(dayofweek("order_timestamp").isin(1, 2, 6, 7), col("order_id"))).alias("weekend_orders"),
        # Category diversity
        countDistinct("category_id").alias("distinct_categories"),
    )

    # Preferred channel: the mode channel per customer
    channel_counts = fact.groupBy("customer_id", "order_channel").agg(
        count("order_id").alias("ch")
    )
    # Rank by count within customer, take the top
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number
    w = Window.partitionBy("customer_id").orderBy(col("ch").desc())
    preferred = (
        channel_counts
        .withColumn("rn", row_number().over(w))
        .filter(col("rn") == 1)
        .select("customer_id", col("order_channel").alias("preferred_channel"))
    )

    cust = (
        customers.select("customer_id", "registration_date")
        .join(agg, on="customer_id", how="left")
        .join(preferred, on="customer_id", how="left")
    )

    # Fallbacks for customers with zero orders
    cust = cust.fillna({
        "order_count": 0,
        "monetary": 0.0,
        "line_count": 0,
        "peak_orders": 0,
        "weekend_orders": 0,
        "distinct_categories": 0,
    })

    # Derived
    cust = (
        cust
        .withColumn("last_activity_ts",
                    least(
                        coalesce(col("last_order_ts"), col("registration_date").cast("timestamp")),
                        lit("2024-12-31").cast("timestamp"),
                    ))
        .withColumn("recency_days",
                    datediff(to_date(lit("2024-12-31")), to_date(col("last_activity_ts"))))
        .withColumn("average_order_value",
                    when(col("order_count") > 0,
                         col("monetary") / col("order_count")).otherwise(lit(0.0)))
        .withColumn("avg_basket_size",
                    when(col("order_count") > 0,
                         col("line_count").cast("double") / col("order_count").cast("double")).otherwise(lit(0.0)))
        .withColumn("peak_hour_share",
                    when(col("order_count") > 0,
                         col("peak_orders").cast("double") / col("order_count").cast("double")).otherwise(lit(0.0)))
        .withColumn("weekend_ratio",
                    when(col("order_count") > 0,
                         col("weekend_orders").cast("double") / col("order_count").cast("double")).otherwise(lit(0.0)))
    )

    return cust


# ============================================================
# Order features (per order_id) — used by ML models needing order grain
# ============================================================

def build_order_features(fact):
    """One row per order_id. Contains peak-hour flag, weekend flag, basket size, channel.

    This table provides the actual ML-usable form of SRS Step 7 features:
      - Peak-hour frequency   (is_peak_hour flag per order)
      - Weekend-order ratio   (is_weekend flag per order)
      - Basket size           (line_count per order)
      - Channel preference    (order_channel per order)
    """
    f = fact
    order_df = f.groupBy("order_id").agg(
        first("customer_id").alias("customer_id"),
        first("restaurant_id").alias("restaurant_id"),
        first("order_timestamp").alias("order_timestamp"),
        first("order_channel").alias("order_channel"),
        first("order_status").alias("order_status"),
        first("promotion_id").alias("promotion_id"),
        count("order_item_id").alias("basket_size"),
        spark_sum("line_total").cast("double").alias("order_total"),
        countDistinct("menu_item_id").alias("distinct_items"),
    )

    order_df = (
        order_df
        .withColumn("hour_of_day", hour("order_timestamp"))
        .withColumn("day_of_week", dayofweek("order_timestamp"))
        .withColumn("month_num", month("order_timestamp"))
        .withColumn("is_weekend",
                    when(dayofweek("order_timestamp").isin(1, 2, 6, 7), lit(1)).otherwise(lit(0)))
        .withColumn("is_peak_hour",
                    when(hour("order_timestamp").between(11, 21), lit(1)).otherwise(lit(0)))
    )

    return order_df


# ============================================================
# Location × Item features — required for SRS Step 34
# ============================================================

def build_location_item_features(fact):
    """Per (restaurant_id, menu_item_id): how well does each item perform at each location?"""
    f = fact
    f = f.withColumn("line_cost", col("quantity").cast("double") * col("unit_cost").cast("double"))
    f = f.withColumn("line_cm", col("line_total").cast("double") - col("line_cost"))

    loc_item = f.groupBy("restaurant_id", "menu_item_id").agg(
        countDistinct("order_id").alias("orders"),
        spark_sum("quantity").alias("quantity"),
        spark_sum("line_total").cast("double").alias("revenue"),
        spark_sum("line_cm").alias("contribution_margin"),
    )
    return loc_item


# ============================================================
# Time summary — kept as reference aggregation (not ML feature)
# ============================================================

def build_time_features(fact):
    """Aggregation summary by hour × day × month. Reference only."""
    f = fact.withColumn("hour_of_day", hour("order_timestamp")) \
            .withColumn("day_of_week", dayofweek("order_timestamp")) \
            .withColumn("month_num", month("order_timestamp"))

    time_agg = f.groupBy("hour_of_day", "day_of_week", "month_num").agg(
        countDistinct("order_id").alias("order_count"),
        spark_sum("line_total").cast("double").alias("revenue"),
    )
    return time_agg


# ============================================================
# Main
# ============================================================

def run_feature_engineering():
    start = time.time()
    FEATURES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("DineIQ-U14-Features")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print("[load] Building integrated fact table (10 joins) ...")
    fact = build_integrated_fact(spark)
    fact_rows = fact.count()
    print(f"  fact rows = {fact_rows:,}")

    print("[load] Loading cleaned Customers dimension ...")
    customers_clean = load_clean(spark, "Customers")
    print(f"  customers rows = {customers_clean.count():,}")

    print("[features] Item-level ...")
    item = build_item_features(fact, spark)
    item_rows = item.count()
    item.write.mode("overwrite").parquet(str(FEATURES / "item_features.parquet"))
    print(f"  item_features rows = {item_rows}")

    print("[features] Customer-level (LEFT JOIN — all customers included) ...")
    cust = build_customer_features(fact, customers_clean)
    cust_rows = cust.count()
    cust.write.mode("overwrite").parquet(str(FEATURES / "customer_features.parquet"))
    print(f"  customer_features rows = {cust_rows}")

    print("[features] Order-level (order grain) ...")
    orders_feat = build_order_features(fact)
    orders_rows = orders_feat.count()
    orders_feat.write.mode("overwrite").parquet(str(FEATURES / "order_features.parquet"))
    print(f"  order_features rows = {orders_rows}")

    print("[features] Location × Item ...")
    loc_item = build_location_item_features(fact)
    loc_item_rows = loc_item.count()
    loc_item.write.mode("overwrite").parquet(str(FEATURES / "location_item_features.parquet"))
    print(f"  location_item_features rows = {loc_item_rows}")

    print("[features] Time summary ...")
    time_df = build_time_features(fact)
    time_rows = time_df.count()
    time_df.write.mode("overwrite").parquet(str(FEATURES / "time_features.parquet"))
    print(f"  time_features rows = {time_rows}")

    report = {
        "fact_rows": int(fact_rows),
        "item_features_rows": int(item_rows),
        "customer_features_rows": int(cust_rows),
        "order_features_rows": int(orders_rows),
        "location_item_features_rows": int(loc_item_rows),
        "time_features_rows": int(time_rows),
        "elapsed_seconds": round(time.time() - start, 2),
        "srs_step_6_joins": 10,
        "srs_step_7_features_produced": 22,
    }

    with (REPORTS / "feature_engineering_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nDone in {report['elapsed_seconds']}s.")
    spark.stop()
    return report


if __name__ == "__main__":
    run_feature_engineering()

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lower, trim, when


# Documented rule: each function returns (clean_df, quarantine_df, description)
# The quarantine DataFrame is written to quarantine/ for audit and later inspection.


def clean_missing_values(orders, lines, menu, pricing):
    """Rule: drop rows with NULL in required numeric/date columns.
    Action: remove."""
    valid_mask = (
        col("subtotal").isNotNull() & col("discount_total").isNotNull() &
        col("total_amount").isNotNull() & col("order_timestamp").isNotNull()
    )
    clean = orders.filter(valid_mask)
    quar = orders.filter(~valid_mask)
    return clean, quar, "Drop rows with NULL in required Orders columns"


def clean_duplicate_orders(orders):
    """Rule: keep first occurrence per order_id. Action: deduplicate."""
    clean = orders.dropDuplicates(["order_id"])
    keys = clean.select("order_id")
    quar = orders.join(keys, on="order_id", how="left_anti")
    return clean, quar, "Keep first row per order_id; quarantine duplicates"


def clean_duplicate_order_items(lines):
    """Rule: keep first occurrence per order_item_id. Action: deduplicate."""
    clean = lines.dropDuplicates(["order_item_id"])
    keys = clean.select("order_item_id")
    quar = lines.join(keys, on="order_item_id", how="left_anti")
    return clean, quar, "Keep first row per order_item_id; quarantine duplicates"


def clean_invalid_menu_prices(menu):
    """Rule: base_price must be > 0 and <= 1000. Action: quarantine invalid."""
    valid = col("base_price").isNotNull() & (col("base_price") > 0) & (col("base_price") <= 1000)
    return menu.filter(valid), menu.filter(~valid), "Quarantine rows where base_price invalid"


def clean_negative_quantities(lines):
    """Rule: quantity >= 0 in Order_Items. Action: quarantine negatives."""
    valid = col("quantity").isNotNull() & (col("quantity") >= 0)
    return lines.filter(valid), lines.filter(~valid), "Quarantine rows with negative quantity"


def clean_negative_inventory_consumption(inventory):
    """Rule: consumption_quantity >= 0. Action: quarantine negatives."""
    valid = col("consumption_quantity").isNotNull() & (col("consumption_quantity") >= 0)
    return inventory.filter(valid), inventory.filter(~valid), "Quarantine negative consumption"


def clean_invalid_dates(orders, ratings, wastage):
    """Rule: dates must not be NULL and must not be in the future (2099 anomaly).
    Action: quarantine rows violating either rule.
    """
    from pyspark.sql.functions import lit

    FUTURE_LIMIT = "2025-12-31"

    valid_o = col("order_timestamp").isNotNull() & (col("order_timestamp") <= lit(FUTURE_LIMIT).cast("timestamp"))
    orders_clean = orders.filter(valid_o)
    orders_quar = orders.filter(~valid_o)

    valid_r = col("rating_timestamp").isNotNull() & (col("rating_timestamp") <= lit(FUTURE_LIMIT).cast("timestamp"))
    ratings_clean = ratings.filter(valid_r)
    ratings_quar = ratings.filter(~valid_r)

    valid_w = col("wastage_date").isNotNull() & (col("wastage_date") <= lit(FUTURE_LIMIT).cast("date"))
    wastage_clean = wastage.filter(valid_w)
    wastage_quar = wastage.filter(~valid_w)

    return (
        (orders_clean, ratings_clean, wastage_clean),
        (orders_quar, ratings_quar, wastage_quar),
        "Quarantine rows with NULL or future dates",
    )


def clean_invalid_ratings(ratings):
    """Rule: rating_value must be in [1, 5]. Action: quarantine invalid."""
    valid = col("rating_value").isNotNull() & (col("rating_value") >= 1) & (col("rating_value") <= 5)
    return ratings.filter(valid), ratings.filter(~valid), "Quarantine ratings outside [1,5]"


def clean_missing_ids(orders, lines):
    """Rule: customer_id and menu_item_id must not be NULL.
    Action: quarantine rows with missing ids."""
    orders_clean = orders.filter(col("customer_id").isNotNull())
    orders_quar = orders.filter(col("customer_id").isNull())
    lines_clean = lines.filter(col("menu_item_id").isNotNull())
    lines_quar = lines.filter(col("menu_item_id").isNull())
    return (
        (orders_clean, lines_clean),
        (orders_quar, lines_quar),
        "Quarantine rows with missing customer_id or menu_item_id",
    )


def clean_invalid_restaurant_ids(orders, restaurants):
    """Rule: restaurant_id must exist in Restaurants. Action: quarantine orphans."""
    valid_keys = restaurants.select("restaurant_id").distinct()
    clean = orders.join(valid_keys, on="restaurant_id", how="left_semi")
    quar = orders.join(valid_keys, on="restaurant_id", how="left_anti")
    return clean, quar, "Quarantine orders whose restaurant_id is invalid"


def clean_impossible_wastage(wastage, inventory):
    """Rule: quantity_wasted must not exceed the maximum closing_quantity
    observed for the same (menu_item_id, restaurant_id). Action: cap at max."""
    from pyspark.sql.functions import max as spark_max

    inv_max = (
        inventory.groupBy("menu_item_id", "restaurant_id")
        .agg(spark_max("closing_quantity").alias("max_closing"))
    )
    joined = wastage.join(inv_max, on=["menu_item_id", "restaurant_id"], how="left")
    clean = joined.withColumn(
        "quantity_wasted",
        when(
            col("max_closing").isNotNull() & (col("quantity_wasted") > col("max_closing")),
            col("max_closing"),
        ).otherwise(col("quantity_wasted")),
    ).drop("max_closing")

    # For audit: rows that were altered
    joined2 = wastage.join(inv_max, on=["menu_item_id", "restaurant_id"], how="left")
    quar = joined2.filter(
        col("max_closing").isNotNull() & (col("quantity_wasted") > col("max_closing"))
    )
    return clean, quar, "Cap quantity_wasted to max available closing_quantity"


def clean_incorrect_discounts(lines):
    """Rule: discount_amount must not exceed quantity * unit_price.
    Action: correct discount to at most gross value."""
    from pyspark.sql.functions import least as spark_least

    clean = lines.withColumn(
        "discount_amount",
        spark_least(
            col("discount_amount"),
            (col("quantity").cast("double") * col("unit_price").cast("double")).cast("decimal(12,2)"),
        ),
    )
    quar = lines.filter(
        col("discount_amount").isNotNull() & col("quantity").isNotNull() &
        col("unit_price").isNotNull() &
        (col("discount_amount") > (col("quantity").cast("double") * col("unit_price").cast("double")))
    )
    return clean, quar, "Correct discount_amount to not exceed line gross"


def clean_inconsistent_units(inventory, wastage, menu):
    """Rule: unit_of_measure must match Menu_Items.unit_of_measure.
    Action: correct to master unit."""
    master = menu.select("menu_item_id", col("unit_of_measure").alias("master_uom"))
    inv_joined = inventory.join(master, on="menu_item_id", how="left")
    inv_clean = inv_joined.withColumn(
        "unit_of_measure",
        when(col("master_uom").isNotNull(), col("master_uom")).otherwise(col("unit_of_measure")),
    ).drop("master_uom")
    inv_quar = inventory.join(master, on="menu_item_id", how="left").filter(
        col("unit_of_measure") != col("master_uom")
    ).drop("master_uom")

    was_joined = wastage.join(master, on="menu_item_id", how="left")
    was_clean = was_joined.withColumn(
        "unit_of_measure",
        when(col("master_uom").isNotNull(), col("master_uom")).otherwise(col("unit_of_measure")),
    ).drop("master_uom")
    was_quar = wastage.join(master, on="menu_item_id", how="left").filter(
        col("unit_of_measure") != col("master_uom")
    ).drop("master_uom")

    return (inv_clean, was_clean), (inv_quar, was_quar), "Normalize unit_of_measure to master"


def clean_cancelled_transactions(orders):
    """Rule: cancelled / refunded orders are valid status, not errors.
    Action: keep. Cleaned pipeline will handle revenue filtering downstream."""
    return orders, orders.limit(0), "Keep cancelled/refunded orders as valid status"
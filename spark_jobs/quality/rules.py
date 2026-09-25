from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lower


def check_missing_values(orders, lines, menu, pricing):
    missing_cols = {}
    for name, df, cols in [
        ("Orders", orders, ["subtotal", "discount_total", "total_amount", "order_timestamp"]),
        ("Order_Items", lines, ["quantity", "unit_price", "unit_cost", "line_total"]),
        ("Menu_Items", menu, ["base_price", "standard_cost"]),
        ("Pricing_History", pricing, ["unit_price"]),
    ]:
        for c in cols:
            n = df.filter(col(c).isNull()).count()
            missing_cols[f"{name}.{c}"] = int(n)
    total = sum(missing_cols.values())
    return {"rule": "DQ1 - Missing values", "total": total, "details": missing_cols}


def check_duplicate_orders(orders):
    total = orders.count()
    distinct = orders.select("order_id").distinct().count()
    return {"rule": "DQ2 - Duplicate orders", "total": total - distinct,
            "distinct_orders": distinct, "total_rows": total}


def check_duplicate_order_items(lines):
    total = lines.count()
    distinct = lines.select("order_item_id").distinct().count()
    return {"rule": "DQ3 - Duplicate order lines", "total": total - distinct,
            "distinct_lines": distinct, "total_rows": total}


def check_invalid_menu_prices(menu):
    bad = menu.filter(
        col("base_price").isNull() | (col("base_price") <= 0) | (col("base_price") > 1000)
    ).count()
    return {"rule": "DQ4 - Invalid menu prices", "total": int(bad)}


def check_negative_quantities(lines, inventory):
    neg_lines = lines.filter(col("quantity") < 0).count()
    neg_inv = inventory.filter(col("consumption_quantity") < 0).count()
    return {"rule": "DQ5 - Negative quantities", "total": int(neg_lines + neg_inv),
            "order_lines": int(neg_lines), "inventory_rows": int(neg_inv)}


def check_invalid_dates(orders, ratings, wastage):
    bad_orders = orders.filter(col("order_timestamp").isNull()).count()
    bad_ratings = ratings.filter(col("rating_timestamp").isNull()).count()
    bad_waste = wastage.filter(col("wastage_date").isNull()).count()
    return {"rule": "DQ6 - Invalid dates", "total": int(bad_orders + bad_ratings + bad_waste),
            "orders": int(bad_orders), "ratings": int(bad_ratings), "wastage": int(bad_waste)}


def check_invalid_ratings(ratings):
    bad = ratings.filter((col("rating_value") < 1) | (col("rating_value") > 5)).count()
    return {"rule": "DQ7 - Invalid ratings", "total": int(bad)}


def check_missing_customer_ids(orders):
    n = orders.filter(col("customer_id").isNull()).count()
    return {"rule": "DQ8 - Missing customer IDs", "total": int(n)}


def check_missing_menu_ids(lines):
    n = lines.filter(col("menu_item_id").isNull()).count()
    return {"rule": "DQ9 - Missing menu IDs", "total": int(n)}


def check_invalid_restaurant_ids(orders, restaurants):
    """Scope: only Orders.restaurant_id."""
    valid = restaurants.select("restaurant_id").distinct()
    bad = (
        orders.filter(col("restaurant_id").isNotNull())
        .join(valid, on="restaurant_id", how="left_anti")
        .count()
    )
    return {"rule": "DQ10 - Invalid restaurant IDs", "total": int(bad)}


def check_impossible_wastage(wastage, inventory):
    inv_max = (
        inventory
        .groupBy("menu_item_id", "restaurant_id")
        .agg({"closing_quantity": "max"})
        .withColumnRenamed("max(closing_quantity)", "max_closing")
    )
    joined = wastage.join(inv_max, on=["menu_item_id", "restaurant_id"], how="inner")
    bad = joined.filter(col("quantity_wasted") > col("max_closing")).count()
    return {"rule": "DQ11 - Impossible wastage", "total": int(bad)}


def check_incorrect_discounts(lines):
    bad = lines.filter(
        col("discount_amount").isNotNull() &
        col("quantity").isNotNull() &
        col("unit_price").isNotNull() &
        (col("discount_amount") > (col("quantity").cast("double") * col("unit_price").cast("double")).cast("decimal(12,2)"))
    ).count()
    return {"rule": "DQ12 - Incorrect discounts", "total": int(bad)}


def check_cancelled_transactions(orders):
    n = orders.filter(lower(col("order_status")) == "cancelled").count()
    return {"rule": "DQ13 - Cancelled transactions", "total": int(n)}


def check_inconsistent_units(inventory, wastage, menu):
    master = menu.select("menu_item_id", col("unit_of_measure").alias("master_uom"))

    inv_bad = (
        inventory.join(master, on="menu_item_id", how="left")
        .filter(col("unit_of_measure").isNotNull() & col("master_uom").isNotNull() &
                (col("unit_of_measure") != col("master_uom")))
        .count()
    )
    was_bad = (
        wastage.join(master, on="menu_item_id", how="left")
        .filter(col("unit_of_measure").isNotNull() & col("master_uom").isNotNull() &
                (col("unit_of_measure") != col("master_uom")))
        .count()
    )
    return {"rule": "DQ14 - Inconsistent units", "total": int(inv_bad + was_bad),
            "inventory": int(inv_bad), "wastage": int(was_bad)}


def check_invalid_location_references(orders, inventory, wastage, restaurants):
    """Invalid location references across ALL fact tables.

    DQ10 checks only Orders.restaurant_id.
    DQ15 broadens the scope to Orders + Inventory + Wastage so that
    referential-integrity concern is covered across every fact table
    that references Restaurants.
    """
    valid = restaurants.select("restaurant_id").distinct()

    ord_bad = (
        orders.filter(col("restaurant_id").isNotNull())
        .join(valid, on="restaurant_id", how="left_anti")
        .count()
    )
    inv_bad = (
        inventory.filter(col("restaurant_id").isNotNull())
        .join(valid, on="restaurant_id", how="left_anti")
        .count()
    )
    was_bad = (
        wastage.filter(col("restaurant_id").isNotNull())
        .join(valid, on="restaurant_id", how="left_anti")
        .count()
    )
    return {
        "rule": "DQ15 - Invalid location references",
        "total": int(ord_bad + inv_bad + was_bad),
        "orders": int(ord_bad),
        "inventory": int(inv_bad),
        "wastage": int(was_bad),
    }

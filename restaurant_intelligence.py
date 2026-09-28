import pandas as pd
from pathlib import Path


# Main project folder
BASE = Path(r"D:\DineIQ")

MENU_PATH = (
    BASE
    / "spark_analytics"
    / "results"
    / "menu_performance_classification.parquet"
)

LOCATION_PATH = (
    BASE
    / "spark_analytics"
    / "results"
    / "tricky_menu_cases_final.parquet"
)

CHANNEL_PATH = (
    BASE
    / "full_output"
    / "processed_data"
    / "features"
    / "customer_features.parquet"
)

OUTPUT_DIR = BASE / "student4" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("Reading menu performance...")
menu = pd.read_parquet(MENU_PATH)

print("Reading location intelligence...")
locations = pd.read_parquet(LOCATION_PATH)

print("Reading customer channel data...")
customers = pd.read_parquet(CHANNEL_PATH)


# ---------------------------------------------------------
# 1. Slow-moving menu items
# ---------------------------------------------------------

slow = (
    menu[menu["sales_level"].astype(str).str.lower() == "low"]
    .copy()
)

slow["finding"] = "Slow-moving menu item"
slow["evidence"] = (
    "Sales level is Low; quantity sold="
    + slow["quantity_sold"].round(0).astype(str)
    + ", revenue="
    + slow["revenue"].round(2).astype(str)
)
slow["action"] = (
    "Review demand and menu placement before increasing production."
)

slow["priority"] = "Medium"

slow_output = slow[
    [
        "menu_item_id",
        "item_name",
        "category_name",
        "quantity_sold",
        "revenue",
        "profit_pct",
        "wastage_pct",
        "promotion_dependency",
        "performance_class",
        "finding",
        "evidence",
        "action",
        "priority",
    ]
].sort_values("quantity_sold")

slow_output.to_parquet(
    OUTPUT_DIR / "slow_moving_dishes.parquet",
    engine="pyarrow",
    index=False,
)


# ---------------------------------------------------------
# 2. Multi-location intelligence
# ---------------------------------------------------------

location = locations.drop_duplicates("menu_item_id").copy()

location["max_location_quantity"] = pd.to_numeric(
    location["max_location_quantity"], errors="coerce"
)

location["min_location_quantity"] = pd.to_numeric(
    location["min_location_quantity"], errors="coerce"
)

location["location_gap"] = (
    location["max_location_quantity"] - location["min_location_quantity"]
)

location["location_ratio"] = (
    location["max_location_quantity"] /
    location["min_location_quantity"].replace(0, pd.NA)
)

location["finding"] = "Different performance across locations"

location["evidence"] = (
    "Maximum location quantity="
    + location["max_location_quantity"].round(0).astype(str)
    + ", minimum="
    + location["min_location_quantity"].round(0).astype(str)
    + ", gap="
    + location["location_gap"].round(0).astype(str)
)

location["action"] = (
    "Review location-level demand and adjust local menu or inventory planning."
)

location["priority"] = "High"

location_output = location[
    [
        "menu_item_id",
        "item_name",
        "location_count",
        "max_location_quantity",
        "min_location_quantity",
        "location_gap",
        "location_ratio",
        "quantity_sold",
        "revenue",
        "case_type",
        "finding",
        "evidence",
        "action",
        "priority",
    ]
].sort_values("location_gap", ascending=False)

location_output.to_parquet(
    OUTPUT_DIR / "location_intelligence.parquet",
    engine="pyarrow",
    index=False,
)


# ---------------------------------------------------------
# 3. Channel analysis
# ---------------------------------------------------------

channel = (
    customers[customers["preferred_channel"].notna()]
    .groupby("preferred_channel")
    .agg(
        customers=("customer_id", "count"),
        orders=("order_count", "sum"),
        revenue=("monetary", "sum"),
        avg_order_value=("average_order_value", "mean"),
        avg_basket_size=("avg_basket_size", "mean"),
        avg_recency=("recency_days", "mean"),
    )
    .reset_index()
)

channel["finding"] = "Customer activity differs by preferred channel"

channel["evidence"] = (
    "Customers="
    + channel["customers"].astype(str)
    + ", orders="
    + channel["orders"].astype(str)
    + ", revenue="
    + channel["revenue"].round(2).astype(str)
)

channel["action"] = (
    "Use channel-specific demand and customer behavior when planning promotions."
)

channel["priority"] = "Medium"

channel.to_parquet(
    OUTPUT_DIR / "channel_intelligence.parquet",
    engine="pyarrow",
    index=False,
)


# ---------------------------------------------------------
# 4. Recommendation engine
# ---------------------------------------------------------

recommendations = []


# Slow-moving recommendations
for _, row in slow_output.head(10).iterrows():
    recommendations.append(
        {
            "finding": row["finding"],
            "evidence": row["evidence"],
            "action": row["action"],
            "priority": row["priority"],
            "source": "menu_performance_classification",
            "menu_item_id": row["menu_item_id"],
            "item_name": row["item_name"],
        }
    )


# Location recommendations
for _, row in location_output.head(10).iterrows():
    recommendations.append(
        {
            "finding": row["finding"],
            "evidence": row["evidence"],
            "action": row["action"],
            "priority": row["priority"],
            "source": "tricky_menu_cases_final",
            "menu_item_id": row["menu_item_id"],
            "item_name": row["item_name"],
        }
    )


# Channel recommendations
for _, row in channel.iterrows():
    recommendations.append(
        {
            "finding": row["finding"],
            "evidence": row["evidence"],
            "action": row["action"],
            "priority": row["priority"],
            "source": "customer_features",
            "menu_item_id": None,
            "item_name": None,
        }
    )


recommendation_output = pd.DataFrame(recommendations)

recommendation_output.to_csv(
    OUTPUT_DIR / "recommendations.csv",
    index=False,
)


# ---------------------------------------------------------
# Final summary
# ---------------------------------------------------------

print()
print("=" * 50)
print("RESTAURANT INTELLIGENCE")
print("=" * 50)

print("Slow-moving items:", len(slow_output))
print("Menu items with location data:", len(location_output))
print("Defined customer channels:", len(channel))
print("Recommendations:", len(recommendation_output))

print()
print("Output folder:")
print(OUTPUT_DIR)

print()
print("Files created:")
print("- slow_moving_dishes.parquet")
print("- location_intelligence.parquet")
print("- channel_intelligence.parquet")
print("- recommendations.csv")

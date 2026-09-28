import os
import pandas as pd


# DineIQ Analytics 
# What-If Scenario Engine
# These scenarios are estimates only.
# No model is retrained and no other pipeline is recalculated.


BASE_PATH = r"D:\DineIQ\spark_analytics\results\menu_profitability.parquet"
OUTPUT_DIR = r"D:\DineIQ\analytical_integration\results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "what_if_results.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# Read the existing Student 2 output

print("Reading menu profitability output...")

df = pd.read_parquet(BASE_PATH)

required = [
    "menu_item_id",
    "item_name",
    "quantity_sold",
    "revenue",
    "cost",
    "contribution_margin",
    "profit_pct",
    "wastage_pct",
    "promotion_dependency",
    "discount_total",
    "min_price",
    "max_price",
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")


# Convert numeric columns to numbers

numeric_cols = [
    "quantity_sold",
    "revenue",
    "cost",
    "contribution_margin",
    "profit_pct",
    "wastage_pct",
    "promotion_dependency",
    "discount_total",
    "min_price",
    "max_price",
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# Use the highest revenue item as the example

# This only selects an item and does not change the original data.
base = df.sort_values("revenue", ascending=False).iloc[0]

item_id = base["menu_item_id"]
item_name = base["item_name"]

base_demand = float(base["quantity_sold"])
base_revenue = float(base["revenue"])
base_cost = float(base["cost"])
base_cm = float(base["contribution_margin"])
base_profit_pct = float(base["profit_pct"])
base_wastage_pct = float(base["wastage_pct"])


# Calculate the average selling price and cost per unit

if base_demand > 0:
    base_price = base_revenue / base_demand
    cost_per_unit = base_cost / base_demand
else:
    base_price = 0
    cost_per_unit = 0


# Calculate one what-if scenario

def calculate_scenario(
    scenario,
    assumption,
    demand_change=0.0,
    price_change=0.0,
    wastage_change=0.0,
    discount_change=0.0,
    promotion_change=0.0,
    removal=False,
    preparation_change=0.0,
):
    """
    Transparent scenario calculator.

    All outputs are estimates.
    """

    demand = base_demand * (1 + demand_change)

    if removal:
        demand = 0

    price = base_price * (1 + price_change)

    revenue = demand * price

    # Estimate operating cost
    cost = demand * cost_per_unit

    # Reduce cost when preparation cost is changed
    cost = cost * (1 - preparation_change)

    # Apply the discount effect
    discount_effect = max(0, discount_change)
    revenue = revenue * (1 - discount_effect)

    # Apply the promotion effect to demand
    if promotion_change != 0:
        revenue_demand_factor = 1 + promotion_change
        demand = demand * revenue_demand_factor

        if removal:
            demand = 0

        revenue = demand * price * (1 - discount_effect)

    # Estimate the new wastage percentage
    wastage_pct = max(0, base_wastage_pct * (1 + wastage_change))

    wastage_cost = cost * (wastage_pct / 100)

    contribution_margin = revenue - cost - wastage_cost

    if revenue > 0:
        profitability = (contribution_margin / revenue) * 100
    else:
        profitability = 0

    return {
        "scenario": scenario,
        "assumption": assumption,
        "estimate_flag": "ESTIMATE - NOT ACTUAL RESULT",
        "menu_item_id": item_id,
        "item_name": item_name,
        "baseline_demand": round(base_demand, 2),
        "estimated_demand": round(demand, 2),
        "baseline_revenue": round(base_revenue, 2),
        "estimated_revenue": round(revenue, 2),
        "baseline_contribution_margin": round(base_cm, 2),
        "estimated_contribution_margin": round(contribution_margin, 2),
        "baseline_wastage_pct": round(base_wastage_pct, 4),
        "estimated_wastage_pct": round(wastage_pct, 4),
        "baseline_profitability_pct": round(base_profit_pct, 4),
        "estimated_profitability_pct": round(profitability, 4),
        "revenue_change": round(revenue - base_revenue, 2),
        "contribution_margin_change": round(
            contribution_margin - base_cm, 2
        ),
        "demand_change": round(demand - base_demand, 2),
    }


# Define the required 8 scenarios

results = []

# 1. Price increase
results.append(
    calculate_scenario(
        "Price Increase",
        "Increase menu price by 10%, assume demand decreases by 5%.",
        demand_change=-0.05,
        price_change=0.10,
    )
)


# 2. Price decrease
results.append(
    calculate_scenario(
        "Price Decrease",
        "Decrease menu price by 10%, assume demand increases by 8%.",
        demand_change=0.08,
        price_change=-0.10,
    )
)


# 3. Discount change
results.append(
    calculate_scenario(
        "Discount Change",
        "Increase effective discount by 5%, assume demand increases by 5%.",
        demand_change=0.05,
        discount_change=0.05,
    )
)


# 4. Promotion frequency
results.append(
    calculate_scenario(
        "Promotion Frequency",
        "Increase promotion-driven demand by 10%.",
        promotion_change=0.10,
    )
)


# 5. Item removal
results.append(
    calculate_scenario(
        "Item Removal",
        "Remove the selected item from the menu.",
        removal=True,
    )
)


# 6. Preparation reduction
results.append(
    calculate_scenario(
        "Preparation Reduction",
        "Reduce preparation-related cost by 10%, demand unchanged.",
        preparation_change=0.10,
    )
)


# 7. Demand change
results.append(
    calculate_scenario(
        "Demand Change",
        "Increase demand by 15%, with price unchanged.",
        demand_change=0.15,
    )
)


# 8. Wastage assumptions
results.append(
    calculate_scenario(
        "Wastage Reduction",
        "Reduce wastage rate by 20%, demand unchanged.",
        wastage_change=-0.20,
    )
)


# Save the scenario results

result_df = pd.DataFrame(results)

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)

print()
print("=" * 60)
print("WHAT-IF SCENARIO ENGINE")
print("=" * 60)

print(f"Demonstration item: {item_name}")
print(f"Menu item ID: {item_id}")
print(f"Scenarios generated: {len(result_df)}")

print()
print("Scenario results:")
print(
    result_df[
        [
            "scenario",
            "estimated_revenue",
            "estimated_contribution_margin",
            "estimated_demand",
            "estimated_wastage_pct",
            "estimated_profitability_pct",
        ]
    ].to_string(index=False)
)

print()
print("Output:")
print(OUTPUT_FILE)
print()
print("NOTE: All scenario values are estimates, not actual results.")

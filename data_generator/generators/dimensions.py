"""
Dimension Tables Generator

Produces: Customers, Restaurants, Menu_Categories, Menu_Items.

Adds launch_date to Menu_Items (SRS Step 11 — "new menu item with
insufficient history"). launch_date is the date the item was introduced,
which may predate its first order. Constraint: launch_date <= first order.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


RESTAURANT_CITIES = [
    "Sanaa", "Aden", "Taiz", "Al Hudaydah", "Ibb",
    "Dhamar", "Al Mukalla", "Sa'dah", "Amran", "Marib",
    "Zinjibar", "Sayun", "Hajjah", "Bajil", "Rada'a",
    "Ataq", "Lahij", "Al Bayda", "Abs", "Ash Shihr",
]

CATEGORY_NAMES = [
    "Appetizers", "Main Course", "Grills", "Seafood", "Beverages",
    "Desserts", "Salads", "Breakfast", "Pasta", "Rice & Sides",
]

CATEGORY_PRICE_RANGE = {
    "Appetizers": (4.0, 12.0),
    "Main Course": (12.0, 30.0),
    "Grills": (14.0, 35.0),
    "Seafood": (16.0, 38.0),
    "Beverages": (2.0, 7.0),
    "Desserts": (3.0, 9.0),
    "Salads": (5.0, 12.0),
    "Breakfast": (4.0, 14.0),
    "Pasta": (10.0, 20.0),
    "Rice & Sides": (4.0, 12.0),
}

CATEGORY_UOM = {
    "Appetizers": "portion",
    "Main Course": "plate",
    "Grills": "portion",
    "Seafood": "plate",
    "Beverages": "glass",
    "Desserts": "portion",
    "Salads": "bowl",
    "Breakfast": "plate",
    "Pasta": "bowl",
    "Rice & Sides": "portion",
}

DISH_NAMES = {
    "Appetizers": ["Hummus", "Baba Ghanoush", "Falafel", "Spring Rolls",
                   "Chicken Wings", "Mozzarella Sticks", "Nachos",
                   "Onion Rings", "Stuffed Vine Leaves", "Cheese Samosa"],
    "Main Course": ["Grilled Chicken", "Beef Steak", "Lamb Chops",
                    "Chicken Curry", "Beef Stew", "Roast Chicken",
                    "Meatballs", "Stuffed Peppers"],
    "Grills": ["Mixed Grill", "Shish Tawook", "Kofta Kebab", "Ribeye Steak",
               "T-Bone Steak", "Lamb Kebab", "Chicken Kebab"],
    "Seafood": ["Grilled Salmon", "Fried Shrimp", "Fish Fillet",
                "Shrimp Scampi", "Calamari", "Grilled Sea Bream"],
    "Beverages": ["Cola", "Lemonade", "Iced Tea", "Orange Juice",
                  "Mango Juice", "Mineral Water", "Fresh Mint Lemonade"],
    "Desserts": ["Cheesecake", "Tiramisu", "Chocolate Cake", "Ice Cream",
                 "Baklava", "Brownie", "Creme Brulee"],
    "Salads": ["Caesar Salad", "Greek Salad", "Tabbouleh", "Fattoush",
               "Garden Salad", "Quinoa Salad"],
    "Breakfast": ["Shakshuka", "Foul Medames", "Omelette", "Pancakes",
                  "French Toast", "Scrambled Eggs"],
    "Pasta": ["Spaghetti Bolognese", "Fettuccine Alfredo",
              "Penne Arrabbiata", "Lasagna", "Carbonara", "Mac & Cheese"],
    "Rice & Sides": ["Steamed Rice", "Fried Rice", "French Fries",
                     "Mashed Potatoes", "Grilled Vegetables", "Garlic Bread"],
}

DESCRIPTION_TEMPLATES = [
    "Freshly prepared {name}.",
    "Signature {name}, cooked to order.",
    "Classic {name} with house sauce.",
    "Chef's {name}, made from quality ingredients.",
    "{name} served with seasonal garnish.",
]

CUSTOMER_SEGMENTS = ["new", "churned", "high_value", "frequent", "occasional"]
SEGMENT_PROBS = {
    "new": 0.10,
    "churned": 0.15,
    "high_value": 0.10,
    "frequent": 0.15,
    "occasional": 0.50,
}


@dataclass
class DimensionState:
    customers: pd.DataFrame
    restaurants: pd.DataFrame
    categories: pd.DataFrame
    menu_items: pd.DataFrame
    location_affinity: np.ndarray


def _pick_indices(rng, n, size, exclude=None):
    exclude = set() if exclude is None else set(int(x) for x in exclude)
    candidates = np.array([i for i in range(n) if i not in exclude], dtype=int)
    size = min(size, len(candidates))
    return rng.choice(candidates, size=size, replace=False)


def _generate_customers(cfg, rng) -> pd.DataFrame:
    n = cfg.n_customers
    customer_ids = np.arange(1, n + 1, dtype=np.int64)

    start = cfg.start
    end = cfg.end
    reg_min = start - pd.Timedelta(days=730)
    total_days = (end - reg_min).days

    segs = rng.choice(
        CUSTOMER_SEGMENTS,
        size=n,
        p=[SEGMENT_PROBS[s] for s in CUSTOMER_SEGMENTS],
    )

    reg_offsets = rng.integers(0, total_days + 1, size=n)

    new_mask = segs == "new"
    if new_mask.any():
        horizon = int(cfg.new_customer_horizon_days)
        new_offsets = total_days - rng.integers(0, horizon + 1, size=int(new_mask.sum()))
        reg_offsets[new_mask] = new_offsets

    churn_mask = segs == "churned"
    if churn_mask.any():
        churn_offsets = rng.integers(0, max(1, total_days - 180), size=int(churn_mask.sum()))
        reg_offsets[churn_mask] = churn_offsets

    reg_dates = reg_min + pd.to_timedelta(reg_offsets, unit="D")

    return pd.DataFrame({
        "customer_id": customer_ids,
        "registration_date": reg_dates.date,
        "_segment": segs,
    })


def _generate_restaurants(cfg, rng) -> pd.DataFrame:
    n = cfg.n_restaurants
    cities = [RESTAURANT_CITIES[i % len(RESTAURANT_CITIES)] for i in range(n)]
    names = [f"DineIQ {cities[i]} Branch {i + 1}" for i in range(n)]
    return pd.DataFrame({
        "restaurant_id": np.arange(1, n + 1, dtype=np.int64),
        "restaurant_name": names,
        "city": cities,
    })


def _generate_categories(cfg, rng) -> pd.DataFrame:
    n = min(cfg.n_categories, len(CATEGORY_NAMES))
    return pd.DataFrame({
        "category_id": np.arange(1, n + 1, dtype=np.int64),
        "category_name": CATEGORY_NAMES[:n],
    })


def _generate_menu_items(cfg, rng, categories: pd.DataFrame):
    n = cfg.n_menu_items
    n_cats = len(categories)
    cat_map = categories.set_index("category_id")["category_name"].to_dict()

    base_per_cat = n // n_cats
    remainder = n % n_cats
    assignment = []
    for i, cid in enumerate(categories["category_id"].values):
        count = base_per_cat + (1 if i < remainder else 0)
        assignment.extend([int(cid)] * count)
    category_assignment = np.array(assignment, dtype=np.int64)
    rng.shuffle(category_assignment)

    item_ids = np.arange(1, n + 1, dtype=np.int64)

    # ----- Flags (orthogonal) -----
    flags = {
        "_is_popular":                rng.random(n) < 0.25,
        "_is_low_margin":             rng.random(n) < 0.20,
        "_is_high_wastage":           rng.random(n) < 0.15,
        "_is_profitable_low_selling": rng.random(n) < 0.12,
        "_is_new_item":               rng.random(n) < 0.08,
        "_is_weekend_only":           rng.random(n) < 0.06,
        "_is_seasonal":               rng.random(n) < 0.10,
        "_is_high_rated_poor_profit": rng.random(n) < 0.06,
        "_is_low_rated_high_sales":   rng.random(n) < 0.06,
        "_is_price_sensitive":        rng.random(n) < 0.15,
        "_is_promo_dependent":        rng.random(n) < 0.15,
    }

    forced_pop_hw = rng.choice(n, size=3, replace=False)
    flags["_is_popular"][forced_pop_hw] = True
    flags["_is_high_wastage"][forced_pop_hw] = True

    popular_pool = np.where(flags["_is_popular"])[0]
    if len(popular_pool) < 5:
        extra = _pick_indices(rng, n, 5 - len(popular_pool), exclude=popular_pool)
        flags["_is_popular"][extra] = True
        popular_pool = np.where(flags["_is_popular"])[0]
    pop_lm_selection = rng.choice(popular_pool, size=5, replace=False)
    flags["_is_low_margin"][pop_lm_selection] = True

    candidates_loss = np.where(flags["_is_popular"] & flags["_is_low_margin"])[0]
    loss_idx = candidates_loss[:3]
    flags["_is_loss_making"] = np.zeros(n, dtype=bool)
    flags["_is_loss_making"][loss_idx] = True
    flags["_is_profitable_low_selling"][flags["_is_loss_making"]] = False

    prof_pool = np.where(flags["_is_profitable_low_selling"])[0]
    if len(prof_pool) >= 2:
        flags["_is_high_rated_poor_profit"][prof_pool[:2]] = True

    hs_pool = np.where(flags["_is_popular"])[0]
    if len(hs_pool) >= 2:
        flags["_is_low_rated_high_sales"][hs_pool[:2]] = True

    # ----- Base price / cost -----
    base_price = np.zeros(n, dtype=float)
    for i in range(n):
        cat_name = cat_map[int(category_assignment[i])]
        lo, hi = CATEGORY_PRICE_RANGE.get(cat_name, (5.0, 20.0))
        base_price[i] = round(float(rng.uniform(lo, hi)), 2)

    standard_cost = np.zeros(n, dtype=float)
    for i in range(n):
        if flags["_is_loss_making"][i]:
            ratio = rng.uniform(1.05, 1.15)
        elif flags["_is_profitable_low_selling"][i]:
            ratio = rng.uniform(0.20, 0.35)
        elif flags["_is_low_margin"][i] or flags["_is_high_rated_poor_profit"][i]:
            ratio = rng.uniform(0.80, 0.92)
        else:
            ratio = rng.uniform(0.35, 0.60)
        standard_cost[i] = round(base_price[i] * ratio, 2)

    uom = np.array([
        CATEGORY_UOM.get(cat_map[int(c)], "portion") for c in category_assignment
    ])

    availability = np.ones(n, dtype=bool)
    availability[rng.random(n) < 0.05] = False

    item_names = []
    for i in range(n):
        cat_name = cat_map[int(category_assignment[i])]
        pool = DISH_NAMES.get(cat_name, [f"{cat_name} Item"])
        item_names.append(pool[i % len(pool)])

    descriptions = [
        DESCRIPTION_TEMPLATES[i % len(DESCRIPTION_TEMPLATES)].format(name=item_names[i])
        for i in range(n)
    ]

    # ----- First available date (internal helper, not saved) -----
    total_days = (cfg.end - cfg.start).days  # 365
    first_available = np.full(n, np.datetime64(cfg.start, "ns"), dtype="datetime64[ns]")
    new_idx = np.where(flags["_is_new_item"])[0]
    if len(new_idx) > 0:
        # New items first appear in the last 60-120 days of the window.
        offsets = rng.integers(total_days - 120, total_days - 60, size=len(new_idx))
        first_available[new_idx] = np.datetime64(cfg.start, "ns") + offsets.astype("timedelta64[D]")

    # ----- launch_date (real column, saved) -----
    # SRS Step 11 requires distinguishing a genuinely new item from an old
    # item whose first order happened late. launch_date is when the item
    # was introduced to the menu. Constraint: launch_date <= first order date.
    launch_dates = []
    for i in range(n):
        if flags["_is_new_item"][i]:
            # New item: launched inside the window, at or before first order.
            first_day = int((first_available[i] - np.datetime64(cfg.start, "ns")) / np.timedelta64(1, "D"))
            launch_offset = max(0, first_day - int(rng.integers(0, 21)))
            launch_dates.append(cfg.start + pd.Timedelta(days=launch_offset))
        else:
            # Existing item: launched 30-365 days before window start.
            launch_offset = int(rng.integers(30, 366))
            launch_dates.append(cfg.start - pd.Timedelta(days=launch_offset))

    # ----- Assemble DataFrame -----
    df = pd.DataFrame({
        "menu_item_id": item_ids,
        "category_id": category_assignment,
        "item_name": item_names,
        "description": descriptions,
        "base_price": base_price,
        "standard_cost": standard_cost,
        "availability": availability,
        "unit_of_measure": uom,
        "launch_date": [d.date() for d in launch_dates],
    })
    for k, v in flags.items():
        df[k] = v
    df["_first_available_date"] = pd.to_datetime(first_available)

    # ----- Location affinity -----
    n_rest = cfg.n_restaurants
    affinity = np.ones((n, n_rest), dtype=float)
    for i in range(n):
        strong = rng.choice(n_rest, size=2, replace=False)
        remaining = np.setdiff1d(np.arange(n_rest), strong)
        weak = rng.choice(remaining, size=2, replace=False)
        affinity[i, strong] *= rng.uniform(3.0, 6.0)
        affinity[i, weak] *= rng.uniform(0.10, 0.25)

    return df, affinity


def generate_dimensions(cfg, rng) -> DimensionState:
    customers = _generate_customers(cfg, rng)
    restaurants = _generate_restaurants(cfg, rng)
    categories = _generate_categories(cfg, rng)
    menu_items, affinity = _generate_menu_items(cfg, rng, categories)

    return DimensionState(
        customers=customers,
        restaurants=restaurants,
        categories=categories,
        menu_items=menu_items,
        location_affinity=affinity,
    )

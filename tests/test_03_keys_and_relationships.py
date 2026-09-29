"""Primary keys and the 10 relationships of SRS Step 6 (+ Promotion_Items junction)."""
import pytest

from .data_access import PRIMARY_KEYS, num, orphan_mask

# The generator duplicates only Orders and Order_Items (anomalies.py), so every
# other table must have a unique primary key.
UNIQUE_KEY_TABLES = ["Customers", "Restaurants", "Menu_Categories", "Menu_Items",
                     "Pricing_History", "Promotions", "Ratings", "Inventory", "Wastage"]

# Master data: every reference must resolve.
STRICT_FKS = [
    ("Menu_Items", "category_id", "Menu_Categories", "category_id"),        # items-categories
    ("Pricing_History", "menu_item_id", "Menu_Items", "menu_item_id"),      # items-pricing
    ("Promotion_Items", "promotion_id", "Promotions", "promotion_id"),
    ("Promotion_Items", "menu_item_id", "Menu_Items", "menu_item_id"),
]
# Raw facts carry intentional invalid references (restaurant_id -999, SRS Step 4): allow 1%.
TOLERANT_FKS = [
    ("Orders", "customer_id", "Customers", "customer_id"),                  # orders-customers
    ("Orders", "restaurant_id", "Restaurants", "restaurant_id"),            # orders-locations
    ("Orders", "promotion_id", "Promotions", "promotion_id"),               # orders-promotions
    ("Order_Items", "order_id", "Orders", "order_id"),                      # orders-order items
    ("Order_Items", "menu_item_id", "Menu_Items", "menu_item_id"),          # order items-menu
    ("Ratings", "menu_item_id", "Menu_Items", "menu_item_id"),              # items-ratings
    ("Ratings", "restaurant_id", "Restaurants", "restaurant_id"),
    ("Ratings", "customer_id", "Customers", "customer_id"),
    ("Inventory", "menu_item_id", "Menu_Items", "menu_item_id"),            # items-inventory
    ("Inventory", "restaurant_id", "Restaurants", "restaurant_id"),
    ("Wastage", "menu_item_id", "Menu_Items", "menu_item_id"),              # items-wastage
    ("Wastage", "restaurant_id", "Restaurants", "restaurant_id"),
]
MAX_ORPHAN_RATE = 0.01


@pytest.mark.parametrize("table", UNIQUE_KEY_TABLES)
def test_primary_key_is_unique(raw, table):
    keys = num(raw(table)[PRIMARY_KEYS[table]])
    dupes = int(keys.duplicated().sum())
    assert dupes == 0, f"{table}: {dupes:,} duplicate {PRIMARY_KEYS[table]} values"


def test_promotion_items_composite_key_is_unique(raw):
    dupes = int(raw("Promotion_Items").duplicated(subset=["promotion_id", "menu_item_id"]).sum())
    assert dupes == 0


@pytest.mark.parametrize("child, fk, parent, pk", STRICT_FKS)
def test_master_foreign_key_resolves(raw, child, fk, parent, pk):
    orphans = int(orphan_mask(raw(child)[fk], raw(parent)[pk]).sum())
    assert orphans == 0, f"{child}.{fk}: {orphans} values not found in {parent}.{pk}"


@pytest.mark.parametrize("child, fk, parent, pk", TOLERANT_FKS)
def test_fact_foreign_key_mostly_resolves(raw, child, fk, parent, pk):
    rate = orphan_mask(raw(child)[fk], raw(parent)[pk]).mean()
    assert rate <= MAX_ORPHAN_RATE, f"{child}.{fk}: {rate:.2%} orphan references"

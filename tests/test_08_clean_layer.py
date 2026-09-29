"""Clean layer (SRS Step 5, FR xv). Skipped until Spark cleaning writes
<DINEIQ_DATA_DIR>/processed_data/clean/ with one Parquet or CSV output per table."""
import pytest

from .data_access import num, orphan_mask

pytestmark = pytest.mark.clean_layer

CLEAN_FKS = [
    ("Orders", "customer_id", "Customers", "customer_id"),
    ("Orders", "restaurant_id", "Restaurants", "restaurant_id"),
    ("Order_Items", "order_id", "Orders", "order_id"),
    ("Order_Items", "menu_item_id", "Menu_Items", "menu_item_id"),
    ("Ratings", "menu_item_id", "Menu_Items", "menu_item_id"),
    ("Wastage", "menu_item_id", "Menu_Items", "menu_item_id"),
    ("Wastage", "restaurant_id", "Restaurants", "restaurant_id"),
]


def _prefer_clean(clean, raw, table):
    """Master tables may not be rewritten by cleaning; fall back to raw for them."""
    try:
        return clean(table)
    except FileNotFoundError:
        return raw(table)


def _clean_or_skip(clean, table):
    try:
        return clean(table)
    except FileNotFoundError:
        pytest.skip(f"{table} not present in clean layer")


def test_orders_have_unique_non_null_ids(clean):
    ids = num(clean("Orders")["order_id"])
    assert ids.notna().all(), "null order_id in clean Orders"
    assert not ids.duplicated().any(), f"{int(ids.duplicated().sum())} duplicate order_id values"


def test_orders_have_customer_and_restaurant(clean):
    orders = clean("Orders")
    for col in ("customer_id", "restaurant_id"):
        assert num(orders[col]).notna().all(), f"null {col} in clean Orders"


def test_order_lines_have_valid_values(clean):
    lines = clean("Order_Items")
    q, p, d = num(lines["quantity"]), num(lines["unit_price"]), num(lines["discount_amount"])
    assert num(lines["menu_item_id"]).notna().all(), "null menu_item_id"
    assert (q > 0).all(), "non-positive quantity"
    assert (p > 0).all(), "non-positive unit_price"
    assert ((d >= 0) & (d <= q * p + 0.01)).all(), "discount outside 0..gross"


def test_ratings_are_whole_stars_1_to_5(clean):
    r = num(_clean_or_skip(clean, "Ratings")["rating_value"])
    assert r.between(1, 5).all() and (r % 1 == 0).all()


def test_wastage_is_not_negative(clean):
    assert (num(_clean_or_skip(clean, "Wastage")["quantity_wasted"]) >= 0).all()


@pytest.mark.parametrize("child, fk, parent, pk", CLEAN_FKS)
def test_foreign_keys_fully_resolve(clean, raw, child, fk, parent, pk):
    orphans = int(orphan_mask(_clean_or_skip(clean, child)[fk],
                              _prefer_clean(clean, raw, parent)[pk]).sum())
    assert orphans == 0, f"{child}.{fk}: {orphans} orphan references after cleaning"


@pytest.mark.parametrize("table", ["Orders", "Order_Items", "Ratings", "Inventory", "Wastage"])
def test_cleaning_never_creates_rows(raw, clean, table):
    assert len(_clean_or_skip(clean, table)) <= len(raw(table))


def test_clean_order_lines_still_meet_srs_minimum(clean):
    rows = len(clean("Order_Items"))
    assert rows >= 1_000_000, (
        f"clean layer has {rows:,} order lines (< 1,000,000). Keep cancelled orders with a "
        "status flag instead of dropping them, or raise the generator volume.")

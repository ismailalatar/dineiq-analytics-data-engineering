"""Dataset minimums from SRS v1.0 section 1.2 ("Hint")."""
import pytest

from .data_access import num, ts

ROW_MINIMUMS = [
    ("Order_Items", 1_000_000),
    ("Customers", 50_000),
    ("Menu_Items", 150),
    ("Menu_Categories", 10),
    ("Restaurants", 20),
    ("Ratings", 100_000),
    ("Wastage", 50_000),
]


@pytest.mark.parametrize("table, minimum", ROW_MINIMUMS)
def test_row_count_meets_srs_minimum(raw, table, minimum):
    rows = len(raw(table))
    assert rows >= minimum, f"{table}: {rows:,} rows < SRS minimum {minimum:,}"


def test_at_least_100k_unique_orders(raw):
    unique = num(raw("Orders")["order_id"]).nunique()
    assert unique >= 100_000, f"only {unique:,} unique orders"


def test_twelve_active_months_of_history(raw):
    """A month counts as active if it holds at least 1% of all orders, so injected
    invalid dates (e.g. 2099-12-31) cannot fake extra months."""
    per_month = ts(raw("Orders")["order_timestamp"]).dt.to_period("M").value_counts()
    active = per_month[per_month >= 0.01 * per_month.sum()]
    assert len(active) >= 12, f"only {len(active)} active months: {sorted(map(str, active.index))}"


def test_multiple_historical_prices(raw):
    history = raw("Pricing_History")
    per_item = num(history["menu_item_id"]).value_counts()
    assert (per_item > 1).any(), "no menu item has more than one price record"
    assert len(history) > len(raw("Menu_Items"))


def test_multiple_promotion_campaigns(raw):
    assert num(raw("Promotions")["promotion_id"]).nunique() >= 2

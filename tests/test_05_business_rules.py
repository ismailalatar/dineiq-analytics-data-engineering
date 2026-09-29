"""Business rules stated in the data dictionary and used by generators/orders.py.
Raw data breaks them on a few injected rows, so most rules must hold for >= 99% of rows."""
from .data_access import num, ts

CHANNELS = {"dine-in", "takeaway", "restaurant website/app",
            "third-party delivery platforms", "other supported channels"}
STATUSES = {"completed", "cancelled", "refunded", "pending"}
MIN_SHARE = 0.99


def _share_in(series, allowed):
    values = series.dropna().astype(str).str.strip().str.lower()
    return values.isin(allowed).mean()


def test_line_total_formula(raw):
    """line_total = quantity * unit_price - discount_amount"""
    lines = raw("Order_Items")
    q, p = num(lines["quantity"]), num(lines["unit_price"])
    d, t = num(lines["discount_amount"]), num(lines["line_total"])
    valid = (q > 0) & (p > 0) & (d >= 0) & t.notna()
    matches = ((q * p - d - t).abs() <= 0.011)[valid]
    assert matches.mean() >= MIN_SHARE, f"only {matches.mean():.2%} of lines match the formula"


def test_order_total_formula(raw):
    """total_amount = subtotal - discount_total"""
    o = raw("Orders")
    s, d, t = num(o["subtotal"]), num(o["discount_total"]), num(o["total_amount"])
    valid = s.notna() & d.notna() & t.notna()
    matches = ((s - d - t).abs() <= 0.011)[valid]
    assert matches.mean() >= MIN_SHARE, f"only {matches.mean():.2%} of orders match the formula"


def test_order_channels_are_documented(raw):
    channels = raw("Orders")["order_channel"]
    assert _share_in(channels, CHANNELS) >= MIN_SHARE
    assert channels.dropna().nunique() >= 4, "SRS Step 35 needs at least 4 ordering channels"


def test_order_statuses_are_documented(raw):
    assert _share_in(raw("Orders")["order_status"], STATUSES) >= MIN_SHARE


def test_ratings_target_an_item_or_a_location(raw):
    r = raw("Ratings")
    has_target = num(r["menu_item_id"]).notna() | num(r["restaurant_id"]).notna()
    assert has_target.mean() >= MIN_SHARE


def test_promotion_end_not_before_start(raw):
    p = raw("Promotions")
    start, end = ts(p["start_date"]), ts(p["end_date"])
    both = start.notna() & end.notna()
    assert (end[both] >= start[both]).all()

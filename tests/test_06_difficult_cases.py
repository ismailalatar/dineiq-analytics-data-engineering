"""The data must contain the difficult cases of SRS Step 11 and section 1.10 item 9.

These tests prove each case EXISTS in the data. The owning module must add its own
test proving it HANDLES the case (see documentation/testing/TEST_PLAN.md section 6).
Thresholds are relative (quantiles, ratios), so they also work on regenerated or
hidden datasets. Mechanisms referenced below are in data_generator/generators/.
"""
import pandas as pd
import pytest

from .data_access import num, plausible_dates, ts


@pytest.fixture(scope="module")
def sales(raw):
    """Valid lines of completed orders with plausible dates, plus header fields and margin."""
    o = raw("Orders")
    head = pd.DataFrame({
        "order_id": num(o["order_id"]), "restaurant_id": num(o["restaurant_id"]),
        "customer_id": num(o["customer_id"]), "promotion_id": num(o["promotion_id"]),
        "order_ts": ts(o["order_timestamp"]),
        "status": o["order_status"].astype(str).str.strip().str.lower(),
    }).drop_duplicates("order_id")
    head = head[(head["status"] == "completed") & plausible_dates(head["order_ts"])]
    lines = raw("Order_Items")
    df = pd.DataFrame({
        "order_id": num(lines["order_id"]), "menu_item_id": num(lines["menu_item_id"]),
        "qty": num(lines["quantity"]), "price": num(lines["unit_price"]),
        "cost": num(lines["unit_cost"]), "line_total": num(lines["line_total"]),
    })
    df = df[(df["qty"] > 0) & (df["price"] > 0) & df["menu_item_id"].notna()]
    df = df.merge(head, on="order_id", how="inner")
    df["margin"] = df["line_total"] - df["qty"] * df["cost"]
    return df


@pytest.fixture(scope="module")
def items(sales):
    g = sales.groupby("menu_item_id")
    out = pd.DataFrame({"qty": g["qty"].sum(), "revenue": g["line_total"].sum(),
                        "margin": g["margin"].sum(), "first_sale": g["order_ts"].min()})
    out["margin_pct"] = out["margin"] / out["revenue"]
    return out


def test_high_selling_loss_making_dish(items):
    """dimensions.py: popular items (4x demand) with cost at 105-115% of price."""
    top_sellers = items[items["qty"] >= items["qty"].quantile(0.75)]
    assert (top_sellers["margin"] < 0).any()


def test_low_selling_high_margin_dish(items):
    """dimensions.py: 0.3x demand with cost at 20-35% of price."""
    low_sellers = items[items["qty"] <= items["qty"].quantile(0.25)]
    assert (low_sellers["margin_pct"] >= items["margin_pct"].quantile(0.75)).any()


def test_popular_dish_with_excessive_wastage(raw, items):
    """dimensions.py forces 3 items to be both popular and high-wastage."""
    w = raw("Wastage")
    wasted = pd.DataFrame({"m": num(w["menu_item_id"]), "q": num(w["quantity_wasted"])})
    wasted = wasted[wasted["q"] > 0].groupby("m")["q"].sum()
    ratio = (wasted / items["qty"]).dropna()
    heavy = ratio[ratio >= 2 * ratio.median()]
    popular = items.index[items["qty"] >= items["qty"].quantile(0.75)]
    assert heavy.index.isin(popular).any()


def test_new_menu_item_with_short_history(sales, items):
    """dimensions.py: new items are first sold in the last 60-120 days of the window."""
    cutoff = sales["order_ts"].max() - pd.Timedelta(days=120)
    assert (items["first_sale"] >= cutoff).any()


def test_dish_performs_differently_across_locations(sales, items):
    """Among items selling at least the median volume, one sells 3x more at its best
    location than at its weakest (random noise alone stays near 1.2x at this volume)."""
    solid = items.index[items["qty"] >= items["qty"].median()]
    by_loc = (sales[sales["menu_item_id"].isin(solid)].dropna(subset=["restaurant_id"])
              .groupby(["menu_item_id", "restaurant_id"])["qty"].sum())
    spread = by_loc.groupby(level=0).agg(lambda s: s.max() / max(s.min(), 1))
    assert (spread >= 3).any()


def test_weekend_only_dish(sales):
    """orders.py: weekend-only items get 15x weekend and 0.2x weekday demand."""
    weekend = sales["qty"].where(sales["order_ts"].dt.dayofweek >= 5, 0)
    share = weekend.groupby(sales["menu_item_id"]).sum() / sales.groupby("menu_item_id")["qty"].sum()
    assert (share >= 0.6).any()   # a normal item sells about 2/7 = 0.29 at weekends


def test_promotion_dependent_dish(raw, sales):
    """orders.py: promotion-dependent items get 5x demand inside their own promotion
    windows and 0.1x outside. A normal item's in-window share tracks window coverage."""
    p, links = raw("Promotions"), raw("Promotion_Items")
    windows = pd.DataFrame({"promotion_id": num(p["promotion_id"]),
                            "start": ts(p["start_date"]).dt.normalize(),
                            "end": ts(p["end_date"]).dt.normalize()}).dropna()
    item_windows = pd.DataFrame({"promotion_id": num(links["promotion_id"]),
                                 "menu_item_id": num(links["menu_item_id"])}
                                ).merge(windows, on="promotion_id")
    calendar = pd.date_range(sales["order_ts"].min().normalize(),
                             sales["order_ts"].max().normalize(), freq="D")
    by_item = dict(tuple(sales.groupby("menu_item_id")))
    for item, win in item_windows.groupby("menu_item_id"):
        if item not in by_item:
            continue
        covered = pd.Series(False, index=calendar)
        for start, end in zip(win["start"], win["end"]):
            covered[start:end] = True
        item_sales = by_item[item]
        in_window = covered.reindex(item_sales["order_ts"].dt.normalize(), fill_value=False)
        share = item_sales["qty"].to_numpy()[in_window.to_numpy()].sum() / item_sales["qty"].sum()
        if share >= 0.6 and share - covered.mean() >= 0.25:
            return
    pytest.fail("no item sells mostly inside its own promotion windows")


def test_churned_customers(sales):
    """orders.py: churned customers place no orders in the last 120 days."""
    end = sales["order_ts"].max()
    per = (sales.dropna(subset=["customer_id"]).groupby("customer_id")
           .agg(orders=("order_id", "nunique"), last=("order_ts", "max")))
    churned = per[(per["orders"] >= 3) & (per["last"] <= end - pd.Timedelta(days=120))]
    assert len(churned) > 0


def test_rating_spike(raw):
    """ratings.py: clusters of 60-120 ratings for one item within 1-2 days.
    Normal volume is about 2 ratings per item per day."""
    r = raw("Ratings")
    df = pd.DataFrame({"m": num(r["menu_item_id"]), "v": num(r["rating_value"]),
                       "d": ts(r["rating_timestamp"]).dt.date}).dropna()
    assert (df.groupby(["m", "d", "v"]).size() >= 10).any()


def test_sales_spike(sales):
    """orders.py: 12 three-day events multiply one item's demand by 10 (or 0.01).
    An item-day at 5x its same-weekday level of the surrounding weeks is a spike;
    comparing like weekdays avoids flagging weekend-only and seasonal items."""
    daily = (sales.assign(day=sales["order_ts"].dt.normalize())
             .groupby(["day", "menu_item_id"])["qty"].sum().unstack(fill_value=0))
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max(), freq="D"),
                          fill_value=0)
    baseline = (pd.concat([daily.shift(k) for k in (-14, -7, 7, 14)])
                .groupby(level=0).median().reindex_like(daily))
    spikes = (daily >= 5 * baseline) & (baseline >= 3)
    assert spikes.to_numpy().any()

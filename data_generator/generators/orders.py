from __future__ import annotations

import numpy as np
import pandas as pd


SRS_CHANNELS = [
    "Dine-in",
    "Takeaway",
    "Restaurant Website/App",
    "Third-party delivery platforms",
    "Other supported channels",
]
SRS_CHANNEL_PROBS = [0.35, 0.22, 0.18, 0.20, 0.05]

SEGMENT_LAMBDA = {
    "high_value": 14.0,
    "frequent":   12.0,
    "new":         8.0,
    "churned":     9.0,
    "occasional":  9.0,
}

HOUR_RANGE = np.arange(8, 24)
HOUR_WEIGHTS = np.array([
    0.5, 0.7, 0.9, 1.5, 2.0, 1.5,
    1.0, 0.8, 0.7, 1.2, 2.2, 2.8,
    2.5, 1.8, 1.0, 0.5,
])
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()


def _build_price_by_day(cfg, pricing_history, menu_items):
    n_items = len(menu_items)
    n_days = (cfg.end - cfg.start).days + 1
    price = np.zeros((n_items, n_days))

    base_prices = menu_items["base_price"].to_numpy(dtype=float)
    for i in range(n_items):
        price[i, :] = base_prices[i]

    ph = pricing_history.copy()
    ph["effective_date"] = pd.to_datetime(ph["effective_date"])
    ph = ph.sort_values(["menu_item_id", "effective_date"])
    for _, row in ph.iterrows():
        item_pos = int(row["menu_item_id"]) - 1
        d = (row["effective_date"] - cfg.start).days
        if 0 <= d < n_days:
            price[item_pos, d:] = float(row["unit_price"])

    return price


def _build_day_item_weights(cfg, rng, state, price_by_day, promotions, promotion_items):
    n_days = (cfg.end - cfg.start).days + 1
    n_items = len(state.menu_items)
    dates = pd.date_range(cfg.start, cfg.end, freq="D")
    dow = dates.dayofweek.to_numpy()
    month = dates.month.to_numpy()

    menu = state.menu_items
    is_popular          = menu["_is_popular"].to_numpy()
    is_profitable_low   = menu["_is_profitable_low_selling"].to_numpy()
    is_new              = menu["_is_new_item"].to_numpy()
    is_weekend_only     = menu["_is_weekend_only"].to_numpy()
    is_seasonal         = menu["_is_seasonal"].to_numpy()
    is_price_sensitive  = menu["_is_price_sensitive"].to_numpy()
    is_low_rated_high   = menu["_is_low_rated_high_sales"].to_numpy()
    is_promo_dep        = menu["_is_promo_dependent"].to_numpy()
    base_prices         = menu["base_price"].to_numpy(dtype=float)
    first_avail         = pd.to_datetime(menu["_first_available_date"]).to_numpy()

    base_w = np.ones(n_items)
    base_w[is_popular]        *= 4.0
    base_w[is_profitable_low] *= 0.30
    base_w[is_new]            *= 0.80
    base_w[is_low_rated_high] *= 2.6

    W = np.tile(base_w, (n_days, 1))

    # Weekend-only items
    weekend_mask = dow >= 5
    for i in np.where(is_weekend_only)[0]:
        W[weekend_mask, i] *= 15.0
        W[~weekend_mask, i] *= 0.20

    # Seasonal items
    for i in np.where(is_seasonal)[0]:
        peak_month = int((i * 7) % 12) + 1
        in_season_months = {(peak_month + k - 1) % 12 + 1 for k in range(3)}
        in_season = np.isin(month, list(in_season_months))
        W[in_season, i] *= 5.0
        W[~in_season, i] *= 0.30

    # New items: zero weight before their first_available_date
    for i in np.where(is_new)[0]:
        avail_day = int((first_avail[i] - np.datetime64(cfg.start, "ns")) / np.timedelta64(1, "D"))
        if avail_day > 0:
            W[:avail_day, i] = 0.0

    # Price-sensitive demand response
    for i in np.where(is_price_sensitive)[0]:
        mult = (base_prices[i] / np.maximum(price_by_day[i, :], 0.01)) ** 2.5
        mult = np.clip(mult, 0.10, 8.0)
        W[:, i] *= mult

    # Promotion-dependent items: 5x demand inside promo windows, 0.1x outside
    if is_promo_dep.any() and len(promotions) > 0:
        promo_items_map = promotion_items.groupby("promotion_id")["menu_item_id"].apply(set).to_dict()
        promo_windows = {}
        for _, prow in promotions.iterrows():
            pid = int(prow["promotion_id"])
            s = (pd.Timestamp(prow["start_date"]) - cfg.start).days
            e = (pd.Timestamp(prow["end_date"]) - cfg.start).days
            promo_windows[pid] = (max(0, s), min(n_days - 1, e))

        menu_ids_arr = menu["menu_item_id"].to_numpy(dtype=int)
        for i in np.where(is_promo_dep)[0]:
            item_id = int(menu_ids_arr[i])
            my_promos = [pid for pid, items in promo_items_map.items() if item_id in items]
            if not my_promos:
                continue
            in_window = np.zeros(n_days, dtype=bool)
            for pid in my_promos:
                if pid in promo_windows:
                    s, e = promo_windows[pid]
                    in_window[s:e + 1] = True
            W[in_window, i] *= 5.0
            W[~in_window, i] *= 0.1

    return W, dates, dow


def _apply_sales_anomalies(cfg, rng, W):
    n_days, n_items = W.shape
    events = []
    for _ in range(12):
        item_idx = int(rng.integers(0, n_items))
        day_idx = int(rng.integers(30, n_days - 30))
        direction = "spike" if rng.random() < 0.5 else "drop"
        lo = max(0, day_idx - 1)
        hi = min(n_days, day_idx + 2)
        if direction == "spike":
            W[lo:hi, item_idx] *= 10.0
        else:
            W[lo:hi, item_idx] *= 0.01
        events.append((direction, item_idx, day_idx))
    return W, events


def generate_orders_and_items(cfg, rng, state, pricing_history, promotions, promotion_items):
    n_orders = int(cfg.n_orders)
    n_days = (cfg.end - cfg.start).days + 1
    menu = state.menu_items
    n_items = len(menu)
    item_ids = menu["menu_item_id"].to_numpy(dtype=int)
    item_costs = menu["standard_cost"].to_numpy(dtype=float)

    price_by_day = _build_price_by_day(cfg, pricing_history, menu)

    W, dates, dow = _build_day_item_weights(
        cfg, rng, state, price_by_day, promotions, promotion_items,
    )
    W, _ = _apply_sales_anomalies(cfg, rng, W)

    affinity = state.location_affinity
    Wt = W[:, None, :] * affinity.T[None, :, :]

    customers = state.customers
    cust_ids_arr = customers["customer_id"].to_numpy(dtype=int)
    cust_seg = customers["_segment"].to_numpy()
    cust_reg = pd.to_datetime(customers["registration_date"]).to_numpy(dtype="datetime64[ns]")
    cust_reg_day = ((cust_reg - np.datetime64(cfg.start, "ns")) / np.timedelta64(1, "D")).astype(int)
    cust_reg_day = np.clip(cust_reg_day, 0, n_days - 1)

    seg_weight = {"high_value": 2.5, "frequent": 2.0, "new": 1.0, "churned": 1.0, "occasional": 1.0}
    cust_w = np.array([seg_weight[s] for s in cust_seg], dtype=float)
    cust_w /= cust_w.sum()

    order_customer_ids = rng.choice(cust_ids_arr, size=n_orders, p=cust_w)
    cust_segment_arr   = cust_seg[order_customer_ids - 1]
    cust_reg_day_arr   = cust_reg_day[order_customer_ids - 1]

    day_w = np.ones(n_days, dtype=float)
    day_w[dow >= 4] *= 1.35
    month_arr = dates.month.to_numpy()
    day_w[month_arr == 12] *= 1.40
    day_w[np.isin(month_arr, [6, 7])] *= 1.20
    day_w /= day_w.sum()

    day_idx_arr = rng.choice(n_days, size=n_orders, p=day_w)

    too_early = day_idx_arr < cust_reg_day_arr
    if too_early.any():
        lo = cust_reg_day_arr[too_early]
        hi = np.full_like(lo, n_days - 1)
        valid = lo <= hi
        new_days = np.full_like(lo, n_days - 1)
        new_days[valid] = (lo[valid] + rng.random(int(valid.sum())) * (hi[valid] - lo[valid] + 1)).astype(int)
        day_idx_arr[too_early] = new_days

    churn_cut_date = (cfg.end - pd.Timedelta(days=cfg.churn_customer_cutoff_days)).normalize()
    churn_cut_day = (churn_cut_date - cfg.start).days
    churn_mask = cust_segment_arr == "churned"
    too_late = churn_mask & (day_idx_arr >= churn_cut_day)
    if too_late.any():
        lo = cust_reg_day_arr[too_late]
        hi = np.full_like(lo, max(0, churn_cut_day - 1))
        valid = lo <= hi
        new_days = np.full_like(lo, max(0, churn_cut_day - 1))
        if valid.any():
            new_days[valid] = (lo[valid] + rng.random(int(valid.sum())) * (hi[valid] - lo[valid] + 1)).astype(int)
        day_idx_arr[too_late] = new_days

    rest_ids_arr = state.restaurants["restaurant_id"].to_numpy(dtype=int)
    order_rest = rng.choice(rest_ids_arr, size=n_orders)

    order_channel = rng.choice(SRS_CHANNELS, size=n_orders, p=SRS_CHANNEL_PROBS)
    order_status = rng.choice(
        ["completed", "cancelled", "refunded", "pending"],
        size=n_orders, p=[0.88, 0.05, 0.05, 0.02],
    )

    order_hours = rng.choice(HOUR_RANGE, size=n_orders, p=HOUR_WEIGHTS)
    order_minutes = rng.integers(0, 60, size=n_orders)
    order_seconds = rng.integers(0, 60, size=n_orders)

    promo_lookup = promotions.set_index("promotion_id")[
        ["start_date", "end_date", "discount_type", "discount_value"]
    ].to_dict("index")
    promo_items_map = promotion_items.groupby("promotion_id")["menu_item_id"].apply(set).to_dict()

    promo_start_day = {}
    promo_end_day = {}
    for pid, row in promo_lookup.items():
        promo_start_day[pid] = (pd.Timestamp(row["start_date"]) - cfg.start).days
        promo_end_day[pid]   = (pd.Timestamp(row["end_date"]) - cfg.start).days

    promo_ids = np.full(n_orders, None, dtype=object)
    wants_promo = rng.random(n_orders) < 0.25
    for i in np.where(wants_promo)[0]:
        d = int(day_idx_arr[i])
        candidates = [pid for pid, sd in promo_start_day.items()
                      if sd <= d <= promo_end_day[pid]]
        if candidates:
            promo_ids[i] = int(rng.choice(candidates))

    lam = np.array([SEGMENT_LAMBDA[s] for s in cust_segment_arr], dtype=float)
    basket_sizes = rng.poisson(lam)
    basket_sizes = np.clip(basket_sizes, 2, 25)
    total_lines = int(basket_sizes.sum())

    all_lines_item = np.empty(total_lines, dtype=int)
    all_lines_order_pos = np.empty(total_lines, dtype=int)
    line_cursor = 0

    for i in range(n_orders):
        k = int(basket_sizes[i])
        d = int(day_idx_arr[i])
        r_pos = int(order_rest[i]) - 1
        w = Wt[d, r_pos, :].astype(float)
        s = w.sum()
        if s <= 0:
            w = np.ones(n_items)
            s = w.sum()
        w = w / s

        chosen = rng.choice(item_ids, size=k, replace=False, p=w)

        pid = promo_ids[i]
        if pid is not None:
            targets = promo_items_map.get(pid, set())
            if len(targets) > 0 and not (set(chosen.tolist()) & targets):
                replacement = int(rng.choice(list(targets)))
                if replacement not in chosen:
                    chosen[0] = replacement

        all_lines_item[line_cursor:line_cursor + k] = chosen
        all_lines_order_pos[line_cursor:line_cursor + k] = i
        line_cursor += k

    quantities = rng.choice(
        [1, 2, 3, 4, 5],
        size=total_lines,
        p=[0.55, 0.22, 0.12, 0.07, 0.04],
    ).astype(float)

    line_days = day_idx_arr[all_lines_order_pos]
    line_unit_price = price_by_day[all_lines_item - 1, line_days]
    line_unit_cost = item_costs[all_lines_item - 1]
    line_gross = quantities * line_unit_price

    discounts = np.zeros(total_lines, dtype=float)
    for idx in range(total_lines):
        oi = all_lines_order_pos[idx]
        pid = promo_ids[oi]
        if pid is None:
            continue
        targets = promo_items_map.get(pid, set())
        if int(all_lines_item[idx]) not in targets:
            continue
        row = promo_lookup[pid]
        if row["discount_type"] == "percentage":
            discounts[idx] = line_gross[idx] * float(row["discount_value"]) / 100.0
        else:
            discounts[idx] = min(float(row["discount_value"]), line_gross[idx])

    discounts = np.round(discounts, 2)
    line_gross = np.round(line_gross, 2)
    line_total = np.round(line_gross - discounts, 2)

    order_items = pd.DataFrame({
        "order_item_id": np.arange(1, total_lines + 1, dtype=np.int64),
        "order_id": (all_lines_order_pos + 1).astype(np.int64),
        "menu_item_id": all_lines_item.astype(np.int64),
        "quantity": quantities,
        "unit_price": np.round(line_unit_price, 2),
        "unit_cost": np.round(line_unit_cost, 2),
        "discount_amount": discounts,
        "line_total": line_total,
    })

    oi_gross = order_items.assign(gross=order_items["quantity"] * order_items["unit_price"])
    agg = oi_gross.groupby("order_id").agg(
        subtotal=("gross", "sum"),
        discount_total=("discount_amount", "sum"),
    ).reset_index()

    orders = pd.DataFrame({
        "order_id": np.arange(1, n_orders + 1, dtype=np.int64),
        "customer_id": order_customer_ids.astype(np.int64),
        "restaurant_id": order_rest.astype(np.int64),
        "promotion_id": promo_ids,
        "order_timestamp": pd.to_datetime(
            np.datetime64(cfg.start, "ns")
            + day_idx_arr.astype("timedelta64[D]")
            + order_hours.astype("timedelta64[h]")
            + order_minutes.astype("timedelta64[m]")
            + order_seconds.astype("timedelta64[s]")
        ),
        "order_channel": order_channel,
        "order_status": order_status,
    })
    orders = orders.merge(agg, on="order_id", how="left")
    orders["subtotal"] = orders["subtotal"].round(2)
    orders["discount_total"] = orders["discount_total"].round(2)
    orders["total_amount"] = (orders["subtotal"] - orders["discount_total"]).round(2)

    orders = orders[[
        "order_id", "customer_id", "restaurant_id", "promotion_id",
        "order_timestamp", "order_channel", "order_status",
        "subtotal", "discount_total", "total_amount",
    ]]

    return orders, order_items
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def _log(results, name, ok, detail=""):
    results.append((name, bool(ok), detail))


def _safe_numeric(s):
    return pd.to_numeric(s, errors="coerce")


def validate_dataset(tables: dict, cfg) -> dict:
    results = []
    tables = {k: v.copy() for k, v in tables.items()}

    orders = tables["Orders"]
    lines = tables["Order_Items"]
    menu = tables["Menu_Items"]
    cust = tables["Customers"]
    rest = tables["Restaurants"]
    cats = tables["Menu_Categories"]
    pricing = tables["Pricing_History"]
    promos = tables["Promotions"]
    promo_items = tables["Promotion_Items"]
    ratings = tables["Ratings"]
    inv = tables["Inventory"]
    waste = tables["Wastage"]

    # ---------------- SRS minimum counts (p.24) ----------------
    # Scale thresholds based on the configured dataset size.
    is_full = cfg.n_orders >= 100_000
    min_orders = 100_000 if is_full else max(100, cfg.n_orders // 2)
    min_lines = 1_000_000 if is_full else max(1000, int(cfg.n_orders * 3))
    min_customers = 50_000 if is_full else max(100, cfg.n_customers // 2)
    min_ratings = 100_000 if is_full else max(100, cfg.n_ratings // 2)
    min_wastage = 50_000 if is_full else max(100, cfg.n_wastage // 2)

    _log(results, f"Orders >= {min_orders:,}",
         orders["order_id"].nunique() >= min_orders,
         f"{orders['order_id'].nunique():,}")
    _log(results, f"Order lines >= {min_lines:,}",
         len(lines) >= min_lines, f"{len(lines):,}")
    _log(results, f"Customers >= {min_customers:,}",
         cust["customer_id"].nunique() >= min_customers,
         f"{cust['customer_id'].nunique():,}")
    _log(results, "Menu items >= 150",
         menu["menu_item_id"].nunique() >= 150, f"{menu['menu_item_id'].nunique()}")
    _log(results, "Categories >= 10",
         cats["category_id"].nunique() >= 10, f"{cats['category_id'].nunique()}")
    _log(results, "Restaurants >= 20",
         rest["restaurant_id"].nunique() >= 20, f"{rest['restaurant_id'].nunique()}")
    _log(results, f"Ratings >= {min_ratings:,}",
         len(ratings) >= min_ratings, f"{len(ratings):,}")
    _log(results, f"Wastage >= {min_wastage:,}",
         len(waste) >= min_wastage, f"{len(waste):,}")
    _log(results, "Pricing records > 150",
         len(pricing) > 150, f"{len(pricing):,}")
    _log(results, "Promotion campaigns >= 2",
         promos["promotion_id"].nunique() >= 2, f"{promos['promotion_id'].nunique()}")

    # ---------------- 12+ months ----------------
    ts = pd.to_datetime(orders["order_timestamp"], errors="coerce").dropna()
    ts_valid = ts[(ts >= cfg.start) & (ts <= cfg.end)]
    span = (ts_valid.max() - ts_valid.min()).days if len(ts_valid) > 0 else 0
    _log(results, "Transaction history >= 12 months", span >= 360, f"{span} days")

    # ---------------- Referential integrity ----------------
    valid_items = set(menu["menu_item_id"])
    valid_rest = set(rest["restaurant_id"])
    valid_cust = set(cust["customer_id"])
    valid_cats = set(cats["category_id"])

    _log(results, "Menu_Items.category_id valid",
         menu["category_id"].isin(valid_cats).all())
    _log(results, "Promotion_Items.promotion_id valid",
         promo_items["promotion_id"].isin(promos["promotion_id"]).all())
    _log(results, "Promotion_Items.menu_item_id valid",
         promo_items["menu_item_id"].isin(valid_items).all())

    # ---------------- SRS Step 4 — 15 DQ cases ----------------
    miss = (orders["subtotal"].isna().sum() +
            lines["unit_cost"].isna().sum() +
            menu["base_price"].isna().sum() +
            pricing["unit_price"].isna().sum())
    _log(results, "DQ1: Missing values", miss > 0, f"{int(miss)} cells")

    _log(results, "DQ2: Duplicate order_ids",
         orders.duplicated(subset=["order_id"]).any(),
         f"{int(orders.duplicated(subset=['order_id']).sum())}")

    _log(results, "DQ3: Duplicate order_item_ids",
         lines.duplicated(subset=["order_item_id"]).any(),
         f"{int(lines.duplicated(subset=['order_item_id']).sum())}")

    bp = _safe_numeric(menu["base_price"])
    _log(results, "DQ4: Invalid menu prices",
         ((bp <= 0) | (bp > 1000)).any(),
         f"{int(((bp <= 0) | (bp > 1000)).sum())}")

    q = _safe_numeric(lines["quantity"])
    _log(results, "DQ5: Negative quantities", (q < 0).any(),
         f"{int((q < 0).sum())}")

    inv_ts = pd.to_datetime(orders["order_timestamp"], errors="coerce").isna().sum()
    _log(results, "DQ6: Invalid dates", inv_ts > 0, f"{int(inv_ts)}")

    rv = _safe_numeric(ratings["rating_value"])
    _log(results, "DQ7: Invalid ratings", ((rv < 1) | (rv > 5)).any(),
         f"{int(((rv < 1) | (rv > 5)).sum())}")

    _log(results, "DQ8: Missing customer IDs",
         orders["customer_id"].isna().any(),
         f"{int(orders['customer_id'].isna().sum())}")

    _log(results, "DQ9: Missing menu IDs",
         lines["menu_item_id"].isna().any(),
         f"{int(lines['menu_item_id'].isna().sum())}")

    inv_rest = _safe_numeric(orders["restaurant_id"])
    bad_rest = int((inv_rest.notna() & ~inv_rest.isin(valid_rest)).sum())
    _log(results, "DQ10: Invalid restaurant IDs",
         bad_rest > 0, f"{bad_rest}")

    inv2 = inv.copy()
    inv2["inventory_date"] = pd.to_datetime(inv2["inventory_date"], errors="coerce")
    inv2 = inv2.sort_values("inventory_date")
    inv_lookup = inv2[["menu_item_id", "restaurant_id", "inventory_date", "closing_quantity"]]
    was2 = waste.copy()
    was2["wastage_date"] = pd.to_datetime(was2["wastage_date"], errors="coerce")
    impossible = 0
    sample = was2.dropna(subset=["wastage_date"]).sample(min(3000, len(was2)), random_state=0)
    for _, row in sample.iterrows():
        sub = inv_lookup[
            (inv_lookup["menu_item_id"] == row["menu_item_id"]) &
            (inv_lookup["restaurant_id"] == row["restaurant_id"]) &
            (inv_lookup["inventory_date"] <= row["wastage_date"])
        ]
        if len(sub) == 0:
            continue
        try:
            if float(pd.to_numeric(row["quantity_wasted"], errors="coerce")) > float(sub["closing_quantity"].iloc[-1]):
                impossible += 1
        except Exception:
            continue
    _log(results, "DQ11: Impossible wastage", impossible > 0, f"{impossible}")

    disc = _safe_numeric(lines["discount_amount"])
    gross = _safe_numeric(lines["quantity"]).abs() * _safe_numeric(lines["unit_price"]).abs()
    _log(results, "DQ12: Incorrect discounts",
         (disc > gross).any(), f"{int((disc > gross).sum())}")

    cancelled = int(orders["order_status"].astype(str).str.lower().eq("cancelled").sum())
    _log(results, "DQ13: Cancelled transactions", cancelled > 0, f"{cancelled}")

    uom_master = menu.set_index("menu_item_id")["unit_of_measure"].to_dict()
    inv_bad = sum(1 for _, r in inv.iterrows()
                  if r["menu_item_id"] in uom_master and pd.notna(r["unit_of_measure"])
                  and r["unit_of_measure"] != uom_master[r["menu_item_id"]])
    was_bad = sum(1 for _, r in waste.iterrows()
                  if r["menu_item_id"] in uom_master and pd.notna(r["unit_of_measure"])
                  and r["unit_of_measure"] != uom_master[r["menu_item_id"]])
    _log(results, "DQ14: Inconsistent units",
         inv_bad + was_bad > 0, f"Inv={inv_bad}, Wast={was_bad}")

    _log(results, "DQ15: Invalid location references",
         bad_rest > 0, f"{bad_rest}")

    # ---------------- Temporal integrity ----------------
    reg_map = cust.set_index("customer_id")["registration_date"]
    orders_reg = pd.to_datetime(orders["customer_id"].map(reg_map), errors="coerce")
    orders_ts = pd.to_datetime(orders["order_timestamp"], errors="coerce")
    violations = ((orders_ts.dt.normalize() < orders_reg) & orders_reg.notna() & orders_ts.notna()).sum()
    _log(results, "No order before registration",
         violations == 0, f"{violations}")

    # ---------------- Financial identity ----------------
    valid_lines = lines[
        lines["quantity"].notna() &
        lines["unit_price"].notna() &
        lines["discount_amount"].notna() &
        lines["line_total"].notna()
    ].copy()
    valid_lines["q"] = _safe_numeric(valid_lines["quantity"])
    valid_lines["up"] = _safe_numeric(valid_lines["unit_price"])
    valid_lines["da"] = _safe_numeric(valid_lines["discount_amount"])
    valid_lines["lt"] = _safe_numeric(valid_lines["line_total"])
    valid_lines = valid_lines[(valid_lines["q"] > 0) & (valid_lines["up"] > 0)]
    if len(valid_lines) > 0:
        consistent = ((valid_lines["lt"] - (valid_lines["q"] * valid_lines["up"] - valid_lines["da"])).abs() <= 0.02).mean()
    else:
        consistent = 0.0
    _log(results, "Financial identity >= 0.90",
         consistent >= 0.90, f"{consistent:.3f}")

    # ---------------- Pattern presence ----------------
    ts_only = pd.to_datetime(orders["order_timestamp"], errors="coerce").dropna()
    weekend = (ts_only.dt.dayofweek >= 4).mean()
    _log(results, "Weekend pattern >= 0.40",
         weekend >= 0.40, f"{weekend:.3f}")

    month_std = ts_only.dt.month.value_counts(normalize=True).std()
    _log(results, "Seasonal pattern (std >= 0.005)",
         month_std >= 0.005, f"{month_std:.4f}")

    peak = ts_only.dt.hour.between(11, 21).mean()
    _log(results, "Peak-hour pattern >= 0.60",
         peak >= 0.60, f"{peak:.3f}")

    # ---------------- Business cases ----------------
    lines_valid = lines.copy()
    lines_valid["quantity"] = _safe_numeric(lines_valid["quantity"])
    lines_valid["unit_price"] = _safe_numeric(lines_valid["unit_price"])
    lines_valid["unit_cost"] = _safe_numeric(lines_valid["unit_cost"])
    lines_valid["discount_amount"] = _safe_numeric(lines_valid["discount_amount"])
    lines_valid["line_total"] = _safe_numeric(lines_valid["line_total"])
    lines_valid = lines_valid.dropna(subset=["menu_item_id", "quantity"])
    lines_valid["gross"] = lines_valid["quantity"] * lines_valid["unit_price"]
    lines_valid["cm"] = lines_valid["line_total"] - lines_valid["quantity"] * lines_valid["unit_cost"]

    item_stats = lines_valid.groupby("menu_item_id").agg(
        qty=("quantity", "sum"),
        cm=("cm", "sum"),
        revenue=("line_total", "sum"),
    ).reset_index()
    item_stats["margin_pct"] = np.where(
        item_stats["revenue"] > 0, item_stats["cm"] / item_stats["revenue"], 0.0
    )

    if len(item_stats) > 0:
        q75 = item_stats["qty"].quantile(0.75)
        q25 = item_stats["qty"].quantile(0.25)
        m75 = item_stats["margin_pct"].quantile(0.75)
        m25 = item_stats["margin_pct"].quantile(0.25)

        pop_lowm = int(((item_stats["qty"] >= q75) & (item_stats["margin_pct"] <= m25)).sum())
        _log(results, "BC1: Popular low-margin items", pop_lowm >= 1, f"{pop_lowm}")

        pop_loss = int(((item_stats["qty"] >= q75) & (item_stats["cm"] < 0)).sum())
        _log(results, "BC2: Popular loss-making items", pop_loss >= 1, f"{pop_loss}")

        prof_lowsell = int(((item_stats["qty"] <= q25) & (item_stats["margin_pct"] >= m75)).sum())
        _log(results, "BC3: Profitable low-selling items", prof_lowsell >= 1, f"{prof_lowsell}")

        was_agg = waste.dropna(subset=["menu_item_id"]).copy()
        was_agg["quantity_wasted"] = _safe_numeric(was_agg["quantity_wasted"])
        waste_by_item = was_agg.groupby("menu_item_id")["quantity_wasted"].sum().reset_index()
        waste_q75 = waste_by_item["quantity_wasted"].quantile(0.75)
        hw_count = int((waste_by_item["quantity_wasted"] >= waste_q75).sum())
        _log(results, "BC4: High-wastage items", hw_count >= 3, f"{hw_count}")

        merged_hw = item_stats.merge(waste_by_item, on="menu_item_id", how="left")
        merged_hw["quantity_wasted"] = merged_hw["quantity_wasted"].fillna(0)
        pop_hw = int(((merged_hw["qty"] >= q75) & (merged_hw["quantity_wasted"] >= waste_q75)).sum())
        _log(results, "BC5: Popular + high-wastage", pop_hw >= 1, f"{pop_hw}")

        r_clean = ratings.dropna(subset=["menu_item_id"]).copy()
        r_clean["rating_value"] = _safe_numeric(r_clean["rating_value"])
        r_clean = r_clean[(r_clean["rating_value"] >= 1) & (r_clean["rating_value"] <= 5)]
        avg_r = r_clean.groupby("menu_item_id")["rating_value"].mean().reset_index()
        merged_r = item_stats.merge(avg_r, on="menu_item_id", how="left")

        hr_pp = int(((merged_r["rating_value"] >= 4.0) & (merged_r["margin_pct"] <= m25)).sum())
        _log(results, "BC6: Highly-rated poor-profitability", hr_pp >= 1, f"{hr_pp}")

        lr_hs = int(((merged_r["rating_value"] <= 2.5) & (merged_r["qty"] >= q75)).sum())
        _log(results, "BC7: Low-rated high-sales", lr_hs >= 1, f"{lr_hs}")

    # Sales anomalies
    line_dt = lines.merge(orders[["order_id", "order_timestamp"]], on="order_id", how="left")
    line_dt["order_timestamp"] = pd.to_datetime(line_dt["order_timestamp"], errors="coerce")
    line_dt["date"] = line_dt["order_timestamp"].dt.normalize()
    line_dt["quantity"] = _safe_numeric(line_dt["quantity"])
    daily = line_dt.dropna(subset=["date", "menu_item_id"]).groupby(
        ["menu_item_id", "date"])["quantity"].sum().reset_index()

    spikes = drops = 0
    for _, g in daily.groupby("menu_item_id"):
        if len(g) < 30:
            continue
        m = g["quantity"].mean()
        if m < 3:
            continue
        if g["quantity"].max() > m * 4:
            spikes += 1
        if g["quantity"].min() < m * 0.15:
            drops += 1
    _log(results, "Sales spike anomalies", spikes >= 1, f"{spikes}")
    _log(results, "Sales drop anomalies", drops >= 1, f"{drops}")

    # Rating anomalies
    r_anom = ratings.dropna(subset=["menu_item_id"]).copy()
    r_anom["rating_value"] = _safe_numeric(r_anom["rating_value"])
    r_anom["rating_timestamp"] = pd.to_datetime(r_anom["rating_timestamp"], errors="coerce")
    r_anom = r_anom[(r_anom["rating_value"] >= 1) & (r_anom["rating_value"] <= 5)]
    r_anom = r_anom.dropna(subset=["rating_timestamp"])
    if len(r_anom) > 0:
        r_anom["_day"] = r_anom["rating_timestamp"].dt.normalize()
        grp = r_anom.groupby(["menu_item_id", "_day"]).agg(
            cnt=("rating_value", "size"),
            mean_r=("rating_value", "mean"),
        ).reset_index()
        thr = grp["cnt"].mean() + 5 * grp["cnt"].std()
        conc = grp[grp["cnt"] > thr]
        spikes_r = int(((conc["cnt"] > thr) & (conc["mean_r"] >= 4.3)).sum())
        drops_r = int(((conc["cnt"] > thr) & (conc["mean_r"] <= 2.2)).sum())
    else:
        conc = pd.DataFrame()
        spikes_r = drops_r = 0
    _log(results, "Rating concentration anomalies", len(conc) >= 1, f"{len(conc)}")
    _log(results, "Rating spike anomalies", spikes_r >= 1, f"{spikes_r}")
    _log(results, "Rating drop anomalies", drops_r >= 1, f"{drops_r}")

    # Promotion traps
    promo_lookup = promos.set_index("promotion_id")[["start_date", "end_date"]].to_dict("index")
    promo_items_map = promo_items.groupby("promotion_id")["menu_item_id"].apply(set).to_dict()

    lines_with_ts = lines.merge(
        orders[["order_id", "order_timestamp", "promotion_id"]],
        on="order_id", how="left",
    )
    lines_with_ts["order_timestamp"] = pd.to_datetime(lines_with_ts["order_timestamp"], errors="coerce")
    lines_with_ts["quantity"] = _safe_numeric(lines_with_ts["quantity"])
    lines_with_ts["line_total"] = _safe_numeric(lines_with_ts["line_total"])
    lines_with_ts["unit_cost"] = _safe_numeric(lines_with_ts["unit_cost"])
    lines_with_ts["cm"] = lines_with_ts["line_total"] - lines_with_ts["quantity"] * lines_with_ts["unit_cost"]

    traps = 0
    for pid, row in promo_lookup.items():
        s = pd.Timestamp(row["start_date"])
        e = pd.Timestamp(row["end_date"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        duration = (e - s).days
        sub = lines_with_ts[lines_with_ts["order_timestamp"].between(s, e)]
        targets = promo_items_map.get(pid, set())
        if len(targets) == 0 or len(sub) < 50:
            continue
        sub_t = sub[sub["menu_item_id"].isin(targets)]
        baseline_start = s - pd.Timedelta(days=duration)
        sub_b = lines_with_ts[
            (lines_with_ts["order_timestamp"] >= baseline_start) &
            (lines_with_ts["order_timestamp"] < s) &
            lines_with_ts["menu_item_id"].isin(targets)
        ]
        if len(sub_b) == 0:
            continue
        units_in = sub_t["quantity"].sum()
        units_base = sub_b["quantity"].sum()
        cm_in = sub_t["cm"].sum()
        cm_base = sub_b["cm"].sum()
        if units_base > 0 and units_in / units_base >= 1.2 and cm_in < cm_base:
            traps += 1
    _log(results, "Promotion traps (sales up, CM down)", traps >= 1, f"{traps}")

    # Promotion dependency
    promo_dependent = 0
    for pid, targets in promo_items_map.items():
        if pid not in promo_lookup:
            continue
        s = pd.Timestamp(promo_lookup[pid]["start_date"])
        e = pd.Timestamp(promo_lookup[pid]["end_date"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        sub = lines_with_ts[lines_with_ts["menu_item_id"].isin(targets)]
        in_w = sub[sub["order_timestamp"].between(s, e)]["quantity"].sum()
        out_w = sub[~sub["order_timestamp"].between(s, e)]["quantity"].sum()
        promo_days = max(1, (e - s).days + 1)
        out_days = max(1, (cfg.end - cfg.start).days - promo_days)
        if in_w / promo_days >= 2 * max(out_w / out_days, 0.1):
            promo_dependent += 1
    _log(results, "Promotion dependency", promo_dependent >= 1, f"{promo_dependent}")

    # Location-specific performance
    loc = line_dt.dropna(subset=["menu_item_id"]).merge(
        orders[["order_id", "restaurant_id"]], on="order_id", how="left",
    )
    loc_stats = loc.groupby(["menu_item_id", "restaurant_id"])["quantity"].sum().reset_index()
    cv = (loc_stats.groupby("menu_item_id")["quantity"].std() /
          loc_stats.groupby("menu_item_id")["quantity"].mean()).dropna()
    loc_spec = int((cv > 0.5).sum())
    _log(results, "Location-specific performance (CV > 0.5)",
         loc_spec >= 5, f"{loc_spec}")

    # Weekend-only items
    line_dt["dow"] = line_dt["order_timestamp"].dt.dayofweek
    line_dt["is_weekend"] = line_dt["dow"] >= 5
    wknd_share = line_dt.dropna(subset=["menu_item_id"]).groupby("menu_item_id")["is_weekend"].mean()
    wknd_only = int((wknd_share > 0.65).sum())
    _log(results, "Weekend-only items (> 65% weekend)",
         wknd_only >= 1, f"{wknd_only}")

    # Seasonal items
    line_dt["month"] = line_dt["order_timestamp"].dt.month
    month_pivot = line_dt.dropna(subset=["menu_item_id", "month"]).groupby(
        ["menu_item_id", "month"])["quantity"].sum().reset_index()
    seasonal_count = 0
    for _, g in month_pivot.groupby("menu_item_id"):
        total = g["quantity"].sum()
        if total > 0 and g["quantity"].max() / total > 0.35:
            seasonal_count += 1
    _log(results, "Seasonal items (peak-month > 35%)",
         seasonal_count >= 1, f"{seasonal_count}")

    # New items with insufficient history
    # New items with insufficient history.
# Reference is the configured window end (not max, which is polluted by 2099 DQ dates).
    reference_end = pd.Timestamp(cfg.end)
    valid_orders_ts = pd.to_datetime(orders["order_timestamp"], errors="coerce")
    valid_mask = valid_orders_ts.between(cfg.start, cfg.end)
    valid_order_ids = set(orders.loc[valid_mask, "order_id"])
    valid_lines = line_dt[line_dt["order_id"].isin(valid_order_ids)]
    first_order = valid_lines.dropna(subset=["menu_item_id"]).groupby(
    "menu_item_id")["order_timestamp"].min()
    new_items = int((first_order > reference_end - pd.Timedelta(days=120)).sum())
    _log(results, "New items with insufficient history",
     new_items >= 1, f"{new_items}")

    # SRS channel names
    expected = {"Dine-in", "Takeaway", "Restaurant Website/App",
                "Third-party delivery platforms", "Other supported channels"}
    actual = set(orders["order_channel"].dropna().unique())
    _log(results, "SRS channel terminology",
         expected.issubset(actual), f"{sorted(actual)}")

    # ---------------- Summary ----------------
    fails = [r for r in results if not r[1]]
    passed = [r for r in results if r[1]]

    print("\n" + "=" * 72)
    print("DINEIQ — FULL VALIDATION")
    print("=" * 72)
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        suffix = f"  [{detail}]" if detail else ""
        print(f"[{mark}] {name}{suffix}")
    print("=" * 72)
    print(f"RESULT: {len(passed)} PASS / {len(fails)} FAIL")
    print("=" * 72)

    return {
        "passed": len(fails) == 0,
        "checks": [{"name": n, "passed": o, "detail": d} for n, o, d in results],
    }


def save_validation_report(validation: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validation, indent=2, default=str), encoding="utf-8")
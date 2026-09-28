"""
نحسب rfm لكل عميل مع ميزات سلوكيه
recency frequency monetary مع تقسيم لمستويات
نضيف الفئه المفضله والقناه المفضله وتفضيل الوقت
المخرجات تروح لمجلد 03_rfm
"""

import pandas as pd

from python_pipeline.config import FEATURE_WINDOW_END, RFM_QUANTILES
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


FEATURES_PATH = (
    "python_pipeline/results/parquet/02_feature_store/customer_features.parquet"
)


def load_customer_features():
    df = pd.read_parquet(FEATURES_PATH)
    log.info(f"customer features: {len(df):,} صف")
    return df


def time_of_day(hour):
    # نصنف الساعه الى فتره
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "night"


def build_behavioral(orders, items, categories):
    # نحسب ميزات سلوكيه لكل عميل من الطلبات
    o = orders.copy()
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["hour"] = o["order_timestamp"].dt.hour
    o["weekend"] = o["order_timestamp"].dt.dayofweek >= 5
    o["peak"] = o["hour"].between(11, 21)

    # نسبه الطلبات في ساعات الذروه
    peak = o.groupby("customer_id")["peak"].mean().rename("peak_ratio")
    weekend = o.groupby("customer_id")["weekend"].mean().rename("weekend_ratio")
    promo = o.assign(had_promo=o["promotion_id"].notna()) \
             .groupby("customer_id")["had_promo"].mean().rename("promo_sensitivity")

    # القناه المفضله
    channel = o.groupby("customer_id")["order_channel"].agg(
        lambda s: s.mode().iloc[0] if len(s.mode()) else None
    ).rename("preferred_channel")

    # تفضيل الوقت
    o["tod"] = o["hour"].apply(time_of_day)
    tod = o.groupby("customer_id")["tod"].agg(
        lambda s: s.mode().iloc[0] if len(s.mode()) else None
    ).rename("time_of_day_preference")

    # ----- ميزات جديده لتحسين churn ---
    # 1. عدد الطلبات في اخر 90 يوم
    ref = pd.Timestamp(FEATURE_WINDOW_END)
    recent_90 = ref - pd.Timedelta(days=90)
    recent_orders = o[o["order_timestamp"] >= recent_90]
    freq_90 = recent_orders.groupby("customer_id")["order_id"].nunique().rename("freq_recent_90d")

    # 2. نسبه الطلبات الحديثه من الاجمالي
    total_freq = o.groupby("customer_id")["order_id"].nunique().rename("total_freq")
    freq_df = pd.concat([freq_90, total_freq], axis=1).fillna(0)
    freq_df["freq_trend"] = (freq_df["freq_recent_90d"] / freq_df["total_freq"].replace(0, 1)).round(4)
    freq_trend = freq_df["freq_trend"]

    # 3. متوسط الايام بين الطلبات
    def avg_gap(s):
        s = s.sort_values()
        if len(s) < 2:
            return 0
        return s.diff().dt.days.mean()
    avg_gap = o.groupby("customer_id")["order_timestamp"].apply(avg_gap).rename("avg_days_between_orders")

    # 4. عدد الفئات الفريده
    merged = items.merge(o[["order_id", "customer_id"]], on="order_id", how="inner")
    menu = load_clean_table("Menu_Items")
    merged = merged.merge(menu[["menu_item_id", "category_id"]], on="menu_item_id", how="left")
    distinct_cat = merged.groupby("customer_id")["category_id"].nunique().rename("distinct_categories")

    # ----- الفئه المفضله ---
    merged = merged.merge(categories, on="category_id", how="left")
    fav_cat = merged.groupby(["customer_id", "category_name"]).size() \
                    .reset_index(name="n") \
                    .sort_values(["customer_id", "n"], ascending=[True, False]) \
                    .drop_duplicates("customer_id")[["customer_id", "category_name"]] \
                    .rename(columns={"category_name": "favorite_category"})

    out = pd.concat([peak, weekend, promo, channel, tod,
                     freq_90, freq_trend, avg_gap, distinct_cat], axis=1).reset_index()
    out = out.merge(fav_cat, on="customer_id", how="left")
    return out


def score_rfm(df):
    # نقسم كل بعد لمستويات من 1 الى 4
    out = df.copy()

    out["r_score"] = pd.qcut(
        out["recency"].rank(method="first"),
        RFM_QUANTILES,
        labels=[4, 3, 2, 1],
    ).astype(int)

    out["f_score"] = pd.qcut(
        out["frequency"].rank(method="first"),
        RFM_QUANTILES,
        labels=[1, 2, 3, 4],
    ).astype(int)

    out["m_score"] = pd.qcut(
        out["monetary"].rank(method="first"),
        RFM_QUANTILES,
        labels=[1, 2, 3, 4],
    ).astype(int)

    out["rfm_sum"] = out["r_score"] + out["f_score"] + out["m_score"]
    out["rfm_string"] = (
        out["r_score"].astype(str)
        + out["f_score"].astype(str)
        + out["m_score"].astype(str)
    )
    return out


def run():
    log.info("نبدا rfm")
    feats = load_customer_features()

    # نجيب الطلبات ونفلتر على نافذه الميزات فقط
    orders = load_clean_table("Orders")
    orders = orders[orders["order_status"] != "cancelled"]
    orders["order_timestamp"] = pd.to_datetime(orders["order_timestamp"])
    cutoff = pd.Timestamp(FEATURE_WINDOW_END) + pd.Timedelta(days=1)
    orders = orders[orders["order_timestamp"] < cutoff]

    # نحتاج التفاصيل والتصنيفات للفئه المفضله
    items = load_clean_table("Order_Items")
    categories = load_clean_table("Menu_Categories")

    beh = build_behavioral(orders, items, categories)

    feats = feats.merge(beh, on="customer_id", how="left")
    fill_cols = ["peak_ratio", "weekend_ratio", "promo_sensitivity"]
    feats[fill_cols] = feats[fill_cols].fillna(0)

    rfm = score_rfm(feats)
    save_stage(rfm, "03_rfm", "customer_rfm.parquet")
    log.info(f"rfm: {len(rfm):,} صف")

    dist = rfm["rfm_sum"].value_counts().sort_index().reset_index()
    dist.columns = ["rfm_sum", "n_customers"]
    save_stage(dist, "03_rfm", "rfm_score_distribution.parquet")
    log.info(f"توزيع الدرجات:\n{dist.to_string(index=False)}")


if __name__ == "__main__":
    run()
"""
نقسم العملاء الى شرائح kmeans
نسوي k=6 حسب متطلبات المشروع
ندخل للkmeans فقط ميزات rfm
نستخدم القناه والوقت والفئه المفضله كخصائص للشرائح
ونسمي كل مجموعه حسب الوسط الحسابي لخصائصها
المخرجات تروح لمجلد 04_segmentation
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from python_pipeline.config import RANDOM_SEED
from python_pipeline.lib.io_helpers import save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


RFM_PATH = "python_pipeline/results/parquet/03_rfm/customer_rfm.parquet"

N_SEGMENTS = 6


def load_rfm():
    df = pd.read_parquet(RFM_PATH)
    log.info(f"rfm: {len(df):,} صف")
    return df


def name_row(row):
    # نسمي كل صف حسب قيم الوسط
    r, f, m = row["r"], row["f"], row["m"]
    promo = row["promo"]
    weekend = row["weekend"]

    # يعتمد على العروض
    if promo >= 0.5:
        return "promotion_driven"

    # عميل نهايه الاسبوع
    if weekend >= 0.7:
        return "weekend_only"

    # اعلى قيمه - كل الابعاد عاليه
    if r >= 3 and f >= 3.5 and m >= 3.5:
        return "high_value_loyal"

    # تكرار عالي لكن قيمته متوسطه
    if f >= 3:
        return "frequent"

    # كان يشتري والان بعيد
    if r <= 2.2 and f >= 1.9 and m >= 1.8:
        return "at_risk"

    # عميل جديد
    if r >= 2 and f <= 2 and m <= 2:
        return "new"

    return "occasional"


def label_segments(df):
    # نسمي كل مجموعه حسب الوسط الحسابي
    # نضيف خصائص القناه والوقت والفئه كنصوص مختصره
    profile = df.groupby("cluster").agg(
        r=("r_score", "mean"),
        f=("f_score", "mean"),
        m=("m_score", "mean"),
        promo=("promo_sensitivity", "mean"),
        weekend=("weekend_ratio", "mean"),
        n=("customer_id", "count"),
    ).round(3).reset_index()

    # نضيف اهم قناه ووقت وفئه
    def top_value(g, col):
        if col not in g.columns:
            return ""
        vc = g[col].value_counts()
        return vc.index[0] if len(vc) else ""

    rows = []
    for cid, g in df.groupby("cluster"):
        rows.append({
            "cluster": cid,
            "top_channel": top_value(g, "preferred_channel"),
            "top_tod": top_value(g, "time_of_day_preference"),
            "top_category": top_value(g, "favorite_category"),
        })
    extras = pd.DataFrame(rows)
    profile = profile.merge(extras, on="cluster", how="left")

    # نرتب حسب القيمه
    profile = profile.sort_values(
        ["r", "f", "m"], ascending=False
    ).reset_index(drop=True)

    profile["segment"] = profile.apply(name_row, axis=1)

    # نعالج التكرار
    counts = profile["segment"].value_counts()
    seen = {}
    final = []
    for s in profile["segment"]:
        if counts[s] > 1:
            seen[s] = seen.get(s, 0) + 1
            final.append(f"{s}_{seen[s]}")
        else:
            final.append(s)
    profile["segment"] = final

    return profile


def run():
    log.info("نبدا التقسيم")
    rfm = load_rfm()

    # نستخدم فقط ميزات rfm للclustering
    # القناه والوقت والفئه نستخدمها للوصف بعد التقسيم
    feats = ["recency", "frequency", "monetary", "aov"]
    X = rfm[feats].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # نقارن كم k
    k_search = []
    for k in [3, 4, 5, 6, 7, 8]:
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=10)
        lbl = km.fit_predict(X_scaled)
        k_search.append({
            "k": k,
            "silhouette": round(silhouette_score(X_scaled, lbl), 4),
        })
    save_stage(pd.DataFrame(k_search), "04_segmentation",
               "kmeans_k_search.parquet")

    # نشتغل بـ 6
    km = KMeans(n_clusters=N_SEGMENTS, random_state=RANDOM_SEED, n_init=10)
    rfm["cluster"] = km.fit_predict(X_scaled)

    profile = label_segments(rfm)
    save_stage(profile, "04_segmentation", "segment_profiles.parquet")

    name_map = dict(zip(profile["cluster"], profile["segment"]))
    rfm["segment"] = rfm["cluster"].map(name_map)

    save_stage(rfm, "04_segmentation", "customer_segments.parquet")
    log.info(f"خلصنا - {rfm['segment'].nunique()} شرائح")
    log.info(f"\n{profile.to_string(index=False)}")


if __name__ == "__main__":
    run()
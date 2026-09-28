"""
إنشاء ملف 100 حالة اختبار للـ Dual Pipeline.
هذا الملف يُرسل لـ Student 2 لتشغيل Spark على نفس الحالات.
المخرجات: external/dual_test_cases.parquet
"""

from pathlib import Path

import pandas as pd

from python_pipeline.config import RANDOM_SEED
from python_pipeline.lib.io_helpers import load_clean_table
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)

N_CASES = 100

# مسار الإخراج (خارج python_pipeline)
OUTPUT_DIR = Path("external")
OUTPUT_FILE = OUTPUT_DIR / "dual_test_cases.parquet"


def load_features():
    """حمّل customer features + RFM (نفس المستخدمة في churn)"""
    feats = pd.read_parquet(
        "python_pipeline/results/parquet/02_feature_store/customer_features.parquet"
    )
    rfm = pd.read_parquet(
        "python_pipeline/results/parquet/03_rfm/customer_rfm.parquet"
    )
    
    keep = ["customer_id", "r_score", "f_score", "m_score",
            "promo_sensitivity", "peak_ratio", "weekend_ratio"]
    keep = [c for c in keep if c in rfm.columns]
    
    df = feats.merge(rfm[keep], on="customer_id", how="left")
    log.info(f"total customers: {len(df):,}")
    return df


def build_label(df):
    """أضف الـ Label (churn)"""
    from python_pipeline.config import LABEL_WINDOW_START, LABEL_WINDOW_END
    
    o = load_clean_table("Orders")
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    
    start = pd.Timestamp(LABEL_WINDOW_START)
    end = pd.Timestamp(LABEL_WINDOW_END) + pd.Timedelta(days=1)
    
    active = set(
        o[(o["order_timestamp"] >= start) & (o["order_timestamp"] < end)]["customer_id"]
    )
    
    df = df.copy()
    df["bought_later"] = df["customer_id"].isin(active).astype(int)
    df["churn"] = 1 - df["bought_later"]
    df = df[df["frequency"] > 0].reset_index(drop=True)
    return df


def select_test_cases(df):
    """اختر 100 حالة من Test set (الـ recency الأصغر)"""
    df = df.sort_values("recency", ascending=False).reset_index(drop=True)
    
    n = len(df)
    n_test = int(n * 0.2)
    
    # آخر n_test = الأحدث (نفس Temporal Split)
    test_df = df.iloc[-n_test:].copy()
    
    # اختر 100 حالة عشوائية من test (بـ seed ثابت)
    if len(test_df) > N_CASES:
        test_df = test_df.sample(n=N_CASES, random_state=RANDOM_SEED).reset_index(drop=True)
    
    # أضف record_id فريد
    test_df["record_id"] = ["TC_" + str(i+1).zfill(3) for i in range(len(test_df))]
    
    log.info(f"selected {len(test_df)} test cases")
    return test_df


def save_output(df):
    """احفظ الملف"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # الأعمدة المطلوبة
    cols = [
        "record_id",
        "customer_id",
        # Features
        "recency", "frequency", "monetary", "aov",
        "distinct_items", "r_score", "f_score", "m_score",
        "promo_sensitivity", "peak_ratio", "weekend_ratio",
        # Label
        "churn",
    ]
    cols = [c for c in cols if c in df.columns]
    
    output = df[cols].copy()
    output.to_parquet(OUTPUT_FILE, index=False)
    
    log.info(f"✅ saved: {OUTPUT_FILE}")
    log.info(f"   rows: {len(output)}")
    log.info(f"   columns: {list(output.columns)}")
    
    # عرض عينة
    print("\n" + "=" * 80)
    print("Sample of 5 cases:")
    print("=" * 80)
    print(output.head().to_string())
    print("=" * 80)


def run():
    log.info("Creating dual test cases...")
    df = load_features()
    df = build_label(df)
    test_cases = select_test_cases(df)
    save_output(test_cases)
    log.info("Done ✅")


if __name__ == "__main__":
    run()
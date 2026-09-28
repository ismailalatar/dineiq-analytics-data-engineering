"""
إنشاء 100 حالة اختبار للـ Dual Pipeline.

الحالات مأخوذة مباشرة من Churn Test Cohort الأصلي،
بحيث تستخدم Spark و Python نفس الـ records ونفس الـ features.

المخرج:
external/dual_test_cases.parquet
"""

from pathlib import Path

import pandas as pd

from python_pipeline.config import RANDOM_SEED
from python_pipeline.lib.utils import get_logger


log = get_logger(__name__)

N_CASES = 100

INPUT_FILE = Path(
    "python_pipeline/results/parquet/11_churn/churn_dataset.parquet"
)

OUTPUT_DIR = Path("external")
OUTPUT_FILE = OUTPUT_DIR / "dual_test_cases.parquet"


FEATURES = [
    "recency",
    "frequency",
    "monetary",
    "aov",
    "distinct_items",
    "r_score",
    "f_score",
    "m_score",
    "promo_sensitivity",
    "peak_ratio",
    "weekend_ratio",
    "freq_recent_90d",
    "freq_trend",
    "avg_days_between_orders",
    "distinct_categories",
]


def load_test_cohort():
    """تحميل Test Cohort الأصلي من Churn Pipeline."""
    df = pd.read_parquet(INPUT_FILE)

    required = ["customer_id", "churn"] + FEATURES
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    log.info(f"Test cohort loaded: {len(df):,} rows")
    return df[required].copy()


def select_test_cases(df):
    """اختيار 100 حالة ثابتة من نفس Test Cohort."""
    if len(df) < N_CASES:
        raise ValueError(
            f"Test cohort has only {len(df)} rows, "
            f"but {N_CASES} cases are required."
        )

    test_df = (
        df.sample(n=N_CASES, random_state=RANDOM_SEED)
        .reset_index(drop=True)
    )

    test_df.insert(
        0,
        "record_id",
        [f"TC_{i:03d}" for i in range(1, N_CASES + 1)],
    )

    return test_df


def save_output(df):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_parquet(OUTPUT_FILE, index=False)

    log.info(f"Saved: {OUTPUT_FILE}")
    log.info(f"Rows: {len(df)}")
    log.info(f"Columns: {list(df.columns)}")

    print("\n" + "=" * 80)
    print("Dual Pipeline Test Cases")
    print("=" * 80)
    print(df.head().to_string(index=False))
    print("=" * 80)


def run():
    log.info("Creating dual pipeline test cases...")

    test_cohort = load_test_cohort()
    test_cases = select_test_cases(test_cohort)

    save_output(test_cases)

    log.info("Done.")


if __name__ == "__main__":
    run()
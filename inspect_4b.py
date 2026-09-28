import os, glob
import pandas as pd

SEARCH = r"D:\DineIQ"
TARGETS = [
    "recommendations.csv",
    "dual_pipeline_comparison.parquet",
    "slow_moving_dishes.parquet",
    "location_intelligence.parquet",
    "channel_intelligence.parquet",
    "what_if_results.csv",
    "surprise_modification_readiness.csv",
]

for t in TARGETS:
    hits = glob.glob(os.path.join(SEARCH, "**", t), recursive=True)
    print(f"\n=== {t} ===")
    if not hits:
        print("  NOT FOUND")
        continue
    for h in hits:
        try:
            df = pd.read_parquet(h) if h.endswith(".parquet") else pd.read_csv(h)
            print(f"  path: {h}")
            print(f"  rows: {len(df)}")
            print(f"  cols: {list(df.columns)}")
            print(df.head(2).to_string())
        except Exception as e:
            print(f"  error: {e}")
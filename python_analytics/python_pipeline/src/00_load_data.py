"""
نقرا كل الجداول من clean
ونطبع معلومات سريعه عن كل واحد
"""

import pandas as pd

from python_pipeline.config import REQUIRED_TABLES, PARQUET_DIR
from python_pipeline.lib.io_helpers import load_clean_table, save_parquet
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_all():
    data = {}
    info = []
    for name in REQUIRED_TABLES:
        df = load_clean_table(name)
        data[name] = df
        info.append({
            "table": name,
            "rows": int(len(df)),
            "cols": int(df.shape[1]),
            "columns": ", ".join(df.columns),
        })
    return data, info


def run():
    log.info("نبدا التحميل")
    data, info = load_all()

    summary = pd.DataFrame(info)
    save_parquet(summary, PARQUET_DIR / "load_summary.parquet")

    total = summary["rows"].sum()
    log.info(f"خلصنا - {len(summary)} جدول - {total:,} صف")
    return data


if __name__ == "__main__":
    run()
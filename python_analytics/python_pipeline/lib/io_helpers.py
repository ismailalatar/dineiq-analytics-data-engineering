# read + save helpers عشان نفس الاسلوب في كل مكان

from pathlib import Path

import pandas as pd

from python_pipeline.config import CLEAN_DIR, stage_dir
from python_pipeline.lib.utils import get_logger, ensure_dir

log = get_logger(__name__)


def load_clean_table(table_name):
    # نقرا جدول من مخرجات الطالب الاول
    # ممكن يكون ملف واحد او مجلد فيه parts من spark
    path = CLEAN_DIR / f"{table_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"ما لقينا: {path}")

    df = pd.read_parquet(path)
    log.info(f"{table_name}: {len(df):,} rows")
    return df


def save_parquet(df, path):
    # save df to parquet
    path = Path(path)
    ensure_dir(path.parent)
    df.to_parquet(path, index=False)
    log.info(f"parquet: {path} ({len(df):,})")


def save_stage(df, stage_name, filename):
    # نحفظ داخل مجلد المرحله ونرجع المسار
    path = stage_dir(stage_name) / filename
    save_parquet(df, path)
    return path
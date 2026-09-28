def test_clean_dir_exists():
    from python_pipeline.config import CLEAN_DIR
    assert CLEAN_DIR.exists()


def test_required_tables_exist():
    from python_pipeline.config import CLEAN_DIR, REQUIRED_TABLES
    for name in REQUIRED_TABLES:
        assert (CLEAN_DIR / f"{name}.parquet").exists()
from pathlib import Path


def test_validation_outputs_exist():
    base = "python_pipeline/results/parquet/01_validation"
    files = [
        "validation_rows",
        "validation_columns",
        "validation_nulls",
        "validation_dates",
        "validation_summary",
    ]
    for name in files:
        assert Path(f"{base}/{name}.parquet").exists()
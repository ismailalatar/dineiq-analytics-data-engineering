from pathlib import Path


def test_peak_periods_outputs_exist():
    base = "python_pipeline/results/parquet/11_peak_periods"
    for name in ["peaks_by_hour", "peaks_by_day", "peaks_by_weekend",
                 "peaks_by_month", "peaks_by_location",
                 "peaks_by_channel", "peaks_summary"]:
        assert Path(f"{base}/{name}.parquet").exists()


def test_peaks_by_hour_rows():
    import pandas as pd
    df = pd.read_parquet(
        "python_pipeline/results/parquet/11_peak_periods/peaks_by_hour.parquet"
    )
    assert len(df) <= 24
    assert len(df) > 0


def test_peaks_by_day_rows():
    import pandas as pd
    df = pd.read_parquet(
        "python_pipeline/results/parquet/11_peak_periods/peaks_by_day.parquet"
    )
    assert len(df) == 7
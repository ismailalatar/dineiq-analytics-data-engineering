"""Parquet storage (SRS Step 2, FR xviii) must hold exactly the same rows as the CSV."""
import pytest

from .data_access import TABLES


@pytest.mark.parametrize("table", TABLES)
def test_parquet_row_count_matches_csv(raw, parquet, table):
    csv_rows, pq_rows = len(raw(table)), len(parquet(table))
    assert csv_rows == pq_rows, f"{table}: CSV {csv_rows:,} rows vs Parquet {pq_rows:,}"

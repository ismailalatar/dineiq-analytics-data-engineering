"""Schema validation (SRS Step 3, FR xiii) against the data dictionary."""
import pytest

from .data_access import EXPECTED_COLUMNS, PRIMARY_KEYS, TABLES, num

MASTER_TABLES = ["Customers", "Restaurants", "Menu_Categories", "Menu_Items",
                 "Pricing_History", "Promotions"]


@pytest.mark.parametrize("table", TABLES)
def test_raw_csv_has_documented_columns(raw, table):
    missing = set(EXPECTED_COLUMNS[table]) - set(raw(table).columns)
    assert not missing, f"{table} CSV is missing documented columns: {sorted(missing)}"


@pytest.mark.parametrize("table", TABLES)
def test_parquet_has_documented_columns(parquet, table):
    missing = set(EXPECTED_COLUMNS[table]) - set(parquet(table).columns)
    assert not missing, f"{table} Parquet is missing documented columns: {sorted(missing)}"


@pytest.mark.parametrize("table", MASTER_TABLES)
def test_master_primary_key_is_positive_and_not_null(raw, table):
    keys = num(raw(table)[PRIMARY_KEYS[table]])
    assert keys.notna().all(), f"{table}: null or non-numeric primary keys"
    assert (keys > 0).all(), f"{table}: non-positive primary keys"

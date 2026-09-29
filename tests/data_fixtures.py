"""Data-layer fixtures (Student 6), imported by tests/conftest.py.
A layer is skipped (not failed) when its folder does not exist."""
import pytest

from tests.data_access import CLEAN_DIR, PARQUET_DIR, RAW_DIR, read_table

HINT = "Download the dataset (README) or set DINEIQ_DATA_DIR."


class Layer:
    def __init__(self, folder, formats):
        self.folder, self.formats, self._cache = folder, formats, {}

    def __call__(self, table):
        if table not in self._cache:
            self._cache[table] = read_table(self.folder, table, self.formats)
        return self._cache[table]


def _layer_or_skip(folder, formats, hint):
    if not folder.is_dir():
        pytest.skip(f"{folder} not found. {hint}")
    return Layer(folder, formats)


@pytest.fixture(scope="session")
def raw():
    return _layer_or_skip(RAW_DIR, ("csv",), HINT)


@pytest.fixture(scope="session")
def parquet():
    return _layer_or_skip(PARQUET_DIR, ("parquet",), HINT)


@pytest.fixture(scope="session")
def clean():
    return _layer_or_skip(CLEAN_DIR, ("parquet", "csv"),
                          "Produced by Spark cleaning (Step 5).")
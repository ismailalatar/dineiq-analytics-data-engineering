"""The raw layer must contain every SRS Step 4 defect type, but only as a minority.

SRS 1.2 ("Hint") requires realistic complexity in the generated data; without these
defects the data-quality engine and cleaning rules would have nothing to prove.
"""
import pytest

from .quality_checks import DEFECT_TYPES, detect

MAX_DEFECT_RATE = 0.10


@pytest.fixture(scope="module")
def defects(raw):
    return detect(raw)


@pytest.mark.parametrize("defect", DEFECT_TYPES)
def test_defect_is_present(defects, defect):
    assert defects[defect]["count"] > 0, f"raw data contains no '{defect}' cases"


@pytest.mark.parametrize("defect", DEFECT_TYPES)
def test_defect_is_a_minority(defects, defect):
    d = defects[defect]
    rate = d["count"] / max(d["rows_checked"], 1)
    assert rate < MAX_DEFECT_RATE, f"'{defect}' affects {rate:.1%} of checked rows"

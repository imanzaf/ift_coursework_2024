import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.utils.search import clean_company_name


@pytest.mark.parametrize(
    "name, expected",
    [
        (
            "Apple Inc.",
            "Apple",
        ),
        (
            "Morgan Stanley & Co.",
            "Morgan Stanley",
        ),
        (
            "Deutsche Bank AG",
            "Deutsche Bank",
        ),
    ],
)
def test_clean_company_name(name, expected):
    clean_name = clean_company_name(name)
    assert clean_name == expected

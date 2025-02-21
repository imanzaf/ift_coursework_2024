import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company
from src.esg_reports.validate import SearchResultValidator


class TestSearchResultValidator:

    @pytest.mark.parametrize(
        "company, expected",
        [
            (
                Company(
                    symbol="AAPL",
                    security="Apple Inc.",
                    gics_sector="Tech",
                    gics_industry="Tech",
                    country="USA",
                    region="NA",
                ),
                "Apple",
            ),
            (
                Company(
                    symbol="MS",
                    security="Morgan Stanley & Co.",
                    gics_sector="Finance",
                    gics_industry="Banking",
                    country="USA",
                    region="NA",
                ),
                "Morgan Stanley",
            ),
            (
                Company(
                    symbol="DB",
                    security="Deutsche Bank AG",
                    gics_sector="Finance",
                    gics_industry="Banking",
                    country="Germany",
                    region="EU",
                ),
                "Deutsche Bank",
            ),
        ],
    )
    def test_clean_company_name(self, company, expected):
        validator = SearchResultValidator(company=company, search_results=[])
        assert validator.clean_company_name == expected

    def test_validated_results(self, validator_with_results, multiple_search_results):
        # test that only first result returned
        assert validator_with_results.validated_results[0] == multiple_search_results[0]
        assert len(validator_with_results.validated_results) == 2

from datetime import datetime

import pytest

from src.data_models.company import Company, SearchResult
from src.esg_reports.validate import SearchResultValidator


@pytest.fixture
def sample_company():
    return Company(
        symbol="AAPL",
        security="Apple Inc.",
        gics_sector="Information Technology",
        gics_industry="Technology Hardware & Equipment",
        country="United States",
        region="North America",
    )


@pytest.fixture
def multiple_search_results():
    return [
        SearchResult(
            title=f"Apple ESG Report {datetime.now().year}",
            metatag_title="Apple Environmental Report",
            author="Apple Inc.",
            link="https://example.com/apple_esg_2023.pdf",
            snippet="Latest environmental report from Apple",
        ),
        SearchResult(
            title="Apple Sustainability Report",
            metatag_title=None,
            author=None,
            link="https://example.com/apple_sustainability.pdf",
            snippet="Comprehensive sustainability initiatives",
        ),
        SearchResult(
            title="Apple Corporate Responsibility",
            metatag_title="Corporate Responsibility Report",
            author="Apple Corporate",
            link="https://example.com/apple_corporate.pdf",
            snippet="Corporate responsibility and governance",
        ),
    ]


@pytest.fixture
def validator_with_results(
    sample_company, multiple_search_results
) -> SearchResultValidator:
    return SearchResultValidator(
        company=sample_company, search_results=multiple_search_results
    )

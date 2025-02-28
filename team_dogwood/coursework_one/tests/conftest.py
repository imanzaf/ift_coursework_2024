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
            title="Microsoft Report",
            metatag_title="",
            author="Microsoft",
            link="https://example.com/microsoft_report.pdf",
            snippet="Microsoft Sustainability Report",
        ),
    ]


@pytest.fixture
def validator_with_results(sample_company, multiple_search_results):
    return SearchResultValidator(
        company=sample_company, search_results=multiple_search_results
    )


@pytest.fixture
def google_response():
    return [
        {
            "title": "Apple ESG Report 2023",
            "snippet": "Latest environmental report from Apple",
            "link": "https://example.com/apple_esg_2023.pdf",
            "pagemap": {
                "metatags": [
                    {
                        "title": "Apple Environmental Report",
                        "author": "Apple Inc.",
                    }
                ]
            },
        }
    ]

"""
TODO -
    - Methods to validate the retrieved URL contains the correct data
    - methods to sort reports retrieved from google and sustainability reports
"""

import os
import re
import sys
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, PrivateAttr

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company, SearchResult


class SearchResultValidator(BaseModel):
    """
    Validate the search results from google
    """

    company: Company = Field(
        ..., description="The company to validate the search results for"
    )
    search_results: List[SearchResult] = Field(
        ..., description="The search results to validate"
    )

    # set values for current and previous year
    if (
        datetime.now().month < 4
    ):  # If the current month is less than April, the previous year's report is more likely to be available
        _current_year: str = PrivateAttr(str(datetime.now().year - 1))
        _previous_year: str = PrivateAttr(str(datetime.now().year - 2))
    else:
        _current_year: str = PrivateAttr(str(datetime.now().year))
        _previous_year: str = PrivateAttr(str(datetime.now().year - 1))

    # filter name of company for legal suffices and common articles etc.
    _legal_pattern: str = PrivateAttr(
        r"\b(Inc|Ltd|LLC|PLC|Corp|GmbH|S\.A\.|NV|AG|Pty Ltd|Co\., Ltd\.|Pvt\.|Ltd\.)\b[.,\s]*"
    )
    _article_pattern: str = PrivateAttr(r"\b(a|the|and|&|at|of)\b")

    @property
    def clean_company_name(self):
        # Remove all matches of the legal suffix
        cleaned_name = re.sub(
            self._legal_pattern, "", self.company.security, flags=re.IGNORECASE
        ).strip()
        cleaned_name = re.sub(
            self._article_pattern, "", cleaned_name, flags=re.IGNORECASE
        ).strip()
        return cleaned_name

    @property
    def validated_results(self):
        valid_results = []
        for result in self.search_results:
            if self._year_in_result(result) and self._company_name_in_result(result):
                valid_results.append(result)

        # TODO - check keywords in valid results
        return valid_results

    def _year_in_result(self, result: SearchResult):
        """
        Check that current or previous year is in the title, snippet or link
        """
        if (
            any(
                [
                    year in result.title
                    for year in [self._current_year, self._previous_year]
                ]
            )
            or any(
                [
                    year in result.snippet
                    for year in [self._current_year, self._previous_year]
                ]
            )
            or any(
                [
                    year in result.link
                    for year in [self.current_year, self.previous_year]
                ]
            )
        ):
            return True
        return False

    def _company_name_in_result(self, result: SearchResult):
        """
        Check that the company name is in the author field, title, or snippet
        """
        if any(
            [
                self.clean_company_name in metadata
                for metadata in [result.title, result.snippet, result.author]
            ]
        ):
            return True
        return False

    def _keywords_in_result(self, result: SearchResult):
        """
        TODO !!
        Check that ESG keywords are in the title, snippet or link
        """
        pass


if __name__ == "__main__":
    company = Company(
        symbol="AAPL",
        security="Apple Inc.",
        gics_sector="Technology",
        gics_industry="Technology",
        country="USA",
        region="North America",
    )

    results = [
        SearchResult(
            title="Apple ESG Report 2023",
            metatag_title="Apple Inc. (AAPL) ESG Report 2023",
            author="Apple Inc.",
            link="https://www.apple.com/esg-report-2023/",
            snippet="ESG Report 2023",
        )
    ]

    validator = SearchResultValidator(company=company, search_results=results)
    print(validator.clean_company_name)

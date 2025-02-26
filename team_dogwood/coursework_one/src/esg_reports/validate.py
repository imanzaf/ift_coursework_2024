"""
Methods to validate that URLs retrieved from the Google API contains the correct data.
"""

import os
import sys
from datetime import datetime
from typing import List, Union

from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company, ESGReport, SearchResult
from src.utils.search import clean_company_name


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

    # ESG keywords
    _esg_keywords: List[str] = PrivateAttr(
        [
            "esg",
            "environmental",
            "social",
            "governance",
            "sustainability",
            "climate",
            "carbon",
            "emission",
            "responsibility",
            "impact",
        ]
    )

    @property
    def clean_company_name(self) -> str:
        """
        Clean the company name by removing legal suffixes and common articles.
        """
        name = clean_company_name(self.company.security)
        return name

    @property
    def validated_results(self) -> List[ESGReport]:
        """
        Validate search results based on presence of year,company name and keywords.

        Returns
            validated_results (list[ESGReport]): List of validated search results
        """
        valid_results = []
        for result in self.search_results:
            result_year = self._year_in_result(result)
            if result_year is not None and self._company_name_in_result(result):
                valid_results.append(ESGReport(url=result.link, year=result_year))
            elif all(
                [self._company_name_in_result(result), self._keywords_in_result(result)]
            ):
                valid_results.append(ESGReport(url=result.link, year=None))

        return valid_results

    def _year_in_result(self, result: SearchResult) -> Union[str, None]:
        """
        Check that current or previous year is in the title, snippet or link
        """
        if any(
            [
                self._current_year in text
                for text in [result.title, result.snippet, result.link]
            ]
        ):
            return self._current_year
        elif any(
            [
                self._previous_year in text
                for text in [result.title, result.snippet, result.link]
            ]
        ):
            return self._previous_year
        return None

    def _company_name_in_result(self, result: SearchResult) -> bool:
        """
        Check that the company name is in the author field, title, snippet, or link.
        """
        if any(
            [
                self.clean_company_name.lower() in str(metadata).lower()
                for metadata in [
                    result.title,
                    result.snippet,
                    result.author,
                    result.link,
                ]
            ]
        ):
            return True
        return False

    def _keywords_in_result(self, result: SearchResult) -> bool:
        """
        Check that ESG keywords are in the title, snippet or link.
        """
        if (
            any([keyword in result.title.lower() for keyword in self._esg_keywords])
            or any(
                [keyword in result.snippet.lower() for keyword in self._esg_keywords]
            )
            or any([keyword in result.link.lower() for keyword in self._esg_keywords])
        ):
            return True
        return False


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
    logger.info(f"Cleaned Company Name: {validator.clean_company_name}")

"""
Validates search results from Google for ESG reports.
"""

import os
import re
import sys
from datetime import datetime
from typing import List, Union

from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company, ESGReport, SearchResult
from src.utils.search import clean_company_name


class SearchResultValidator(BaseModel):
    """Validates search results from Google for ESG reports.

    This class validates search results based on the presence of:
    - The current or previous year.
    - The company name.
    - ESG-related keywords.

    Attributes:
        company (Company): The company to validate the search results for.
        search_results (List[SearchResult]): The search results to validate.
    """

    company: Company = Field(
        ..., description="The company to validate the search results for."
    )
    search_results: List[SearchResult] = Field(
        ..., description="The search results to validate."
    )

    # Set values for current and previous year
    if (
        datetime.now().month < 4
    ):  # If the current month is less than April, the previous year's report is more likely to be available
        _current_year: int = PrivateAttr((datetime.now().year - 1))
        _previous_year: int = PrivateAttr((datetime.now().year - 2))
    else:
        _current_year: int = PrivateAttr((datetime.now().year))
        _previous_year: int = PrivateAttr((datetime.now().year - 1))

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
        """Cleans the company name by removing legal suffixes and common articles.

        Returns:
            str: The cleaned company name.

        Example:
            >>> company = Company(symbol="AAPL", security="Apple Inc.")
            >>> validator = SearchResultValidator(company=company, search_results=[])
            >>> print(validator.clean_company_name)
            "Apple"
        """
        name = clean_company_name(self.company.security)
        return name

    @property
    def validated_results(self) -> List[ESGReport]:
        """Validates search results based on the presence of year, company name, and keywords.

        Returns:
            List[ESGReport]: A list of validated ESG reports.

        Example:
            >>> company = Company(symbol="AAPL", security="Apple Inc.")
            >>> results = [
            ...     SearchResult(
            ...         title="Apple ESG Report 2023",
            ...         metatag_title="Apple Inc. (AAPL) ESG Report 2023",
            ...         author="Apple Inc.",
            ...         link="https://www.apple.com/esg-report-2023/",
            ...         snippet="ESG Report 2023",
            ...     )
            ... ]
            >>> validator = SearchResultValidator(company=company, search_results=results)
            >>> validated_results = validator.validated_results
            >>> for result in validated_results:
            ...     print(result.url, result.year)
            "https://www.apple.com/esg-report-2023/" 2023
        """
        valid_results = []
        for result in self.search_results:
            result_year = self._year_in_result(result)
            if result_year is not None and self._company_name_in_result(result):
                valid_results.append(ESGReport(url=result.link, year=result_year))
            elif any(
                [self._company_name_in_result(result), self._keywords_in_result(result)]
            ):
                valid_results.append(ESGReport(url=result.link, year=None))

        return valid_results

    def _year_in_result(self, result: SearchResult) -> Union[str, None]:
        """Checks if the current or previous year is in the title, snippet, or link.

        Args:
            result (SearchResult): The search result to validate.

        Returns:
            Union[str, None]: The year if found, otherwise None.

        Example:
            >>> result = SearchResult(
            ...     title="Apple ESG Report 2023",
            ...     snippet="ESG Report 2023",
            ...     link="https://www.apple.com/esg-report-2023/",
            ... )
            >>> validator = SearchResultValidator(company=Company(symbol="AAPL", security="Apple Inc."), search_results=[])
            >>> year = validator._year_in_result(result)
            >>> print(year)
            "2023"
        """
        # find year in title, snippet, or link
        title_year = self._find_year_in_text(result.title)
        snippet_year = self._find_year_in_text(result.snippet)
        link_year = self._find_year_in_text(result.link)

        if title_year:
            return title_year
        elif snippet_year:
            return snippet_year
        elif link_year:
            return link_year
        else:
            return None

    def _company_name_in_result(self, result: SearchResult) -> bool:
        """Checks if the company name is in the author field, title, snippet, or link.

        Args:
            result (SearchResult): The search result to validate.

        Returns:
            bool: True if the company name is found, otherwise False.

        Example:
            >>> result = SearchResult(
            ...     title="Apple ESG Report 2023",
            ...     snippet="ESG Report 2023",
            ...     link="https://www.apple.com/esg-report-2023/",
            ...     author="Apple Inc.",
            ... )
            >>> validator = SearchResultValidator(company=Company(symbol="AAPL", security="Apple Inc."), search_results=[])
            >>> is_valid = validator._company_name_in_result(result)
            >>> print(is_valid)
            True
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
        """Checks if ESG keywords are in the title, snippet, or link.

        Args:
            result (SearchResult): The search result to validate.

        Returns:
            bool: True if ESG keywords are found, otherwise False.

        Example:
            >>> result = SearchResult(
            ...     title="Apple ESG Report 2023",
            ...     snippet="ESG Report 2023",
            ...     link="https://www.apple.com/esg-report-2023/",
            ... )
            >>> validator = SearchResultValidator(company=Company(symbol="AAPL", security="Apple Inc."), search_results=[])
            >>> has_keywords = validator._keywords_in_result(result)
            >>> print(has_keywords)
            True
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

    def _find_year_in_text(self, text: str) -> Union[str, None]:
        """Finds the most recent year in the given text.

        Args:
            text (str): The text to search for years.

        Returns:
            Union[str, None]: The year found (between 2000 and current year), or None if no year is found.

        Example:
            >>> text = "Apple ESG Report 2023"
            >>> validator = SearchResultValidator(company=Company(symbol="AAPL", security="Apple Inc."), search_results=[])
            >>> year = validator._find_year_in_text(text)
            >>> print(year)
            "2023"
        """

        # Pattern to match full years 2000–2099
        full_year_pattern = r"""
            (?<!\d)                       # Not preceded by digit
            (20[0-9]{2})                  # Capture 2000–2099
            (?!\d)                        # Not followed by digit
        """

        # Pattern to match 2-digit abbreviations 00–99 with optional quote, but don't capture the quote
        abbrev_year_pattern = r"""
            (?<!\d)                       # Not part of a larger number
            '?(0[0-9]|[1-9][0-9])         # Optional quote + 00–99, only capture the digits
            (?!\d)
        """

        # Try full year match first
        # Use re.VERBOSE to allow multi-line regex patterns with comments
        full_years = re.findall(full_year_pattern, text, re.VERBOSE)
        if full_years:
            return full_years[0]

        # Fall back to abbreviated years
        abbrev_years = re.findall(abbrev_year_pattern, text, re.VERBOSE)
        if abbrev_years:
            # Convert to full year format (e.g., 25 -> 2025)
            full_year = f"20{abbrev_years[0]}"
            return full_year

        else:
            # If no match found, return None
            return None


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
    logger.info(f"Validated Results: {validator.validated_results}")

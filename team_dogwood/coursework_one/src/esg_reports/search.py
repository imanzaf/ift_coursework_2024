import os
import re
import sys
import time
from datetime import datetime
from typing import List, Union

import requests
from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr
from requests.exceptions import HTTPError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from config.search import search_settings
from src.data_models.company import Company, ESGReport, SearchResult
from src.utils.search import clean_company_name


class Search(BaseModel):
    """Search class for scraping ESG reports from various sources.

    This class provides methods to search for and retrieve ESG (Environmental, Social, and Governance)
    reports for a given company using different sources:

    1. Google Custom Search API - searches for PDF ESG reports.
    2. Sustainability Reports website - scrapes reports from responsibilityreports.com.

    Attributes:
        company (Company): The company to look for ESG reports for.
    """

    company: Company = Field(
        ..., description="The company to look for ESG reports for."
    )

    # Private attributes
    # Google API Config
    _google_api_url: str = PrivateAttr(search_settings.GOOGLE_API_URL)
    _google_api_key: str = PrivateAttr(search_settings.GOOGLE_API_KEY)
    _google_engine_id: str = PrivateAttr(search_settings.GOOGLE_ENGINE_ID)
    # Sustainability Reports URLs
    _sustainability_reports_url: str = PrivateAttr(
        search_settings.SUSTAINABILITY_REPORTS_API_URL
    )

    @property
    def _google_search_query(self) -> str:
        """Generates the Google search query for ESG reports.

        Returns:
            str: The search query string.

        Example:
            >>> search = Search(company=Company(symbol="AAPL", security="Apple Inc."))
            >>> query = search._google_search_query
            >>> print(query)
            "Apple Inc. 2023 ESG report filetype:pdf"
        """
        search_query = f"{self.company.security} {str(datetime.now().year)} ESG report filetype:pdf"
        return search_query

    @property
    def _sustainability_reports_request_url(self) -> str:
        """Generates the URL for searching sustainability reports.

        Returns:
            str: The URL for the sustainability reports search.

        Example:
            >>> search = Search(company=Company(symbol="AAPL", security="Apple Inc."))
            >>> url = search._sustainability_reports_request_url
            >>> print(url)
            "https://sustainabilityreports.com/Companies?search=Apple Inc."
        """
        return f"{self._sustainability_reports_url}/Companies?search={self.company.security}"

    def google(self) -> Union[List[SearchResult], None]:
        """Searches for ESG reports using the Google Custom Search API.

        Returns:
            Union[List[SearchResult], None]: A list of search results or None if no results are found.

        Example:
            >>> search = Search(company=Company(symbol="AAPL", security="Apple Inc."))
            >>> results = search.google()
            >>> if results:
            ...     for result in results:
            ...         print(result.title, result.link)
            ... else:
            ...     print("No results found.")
        """
        params = {
            "q": self._google_search_query,
            "key": self._google_api_key,
            "cx": self._google_engine_id,
            "num": 3,  # Only return top 3 results
            "fields": "items(title,snippet,link,pagemap.metatags)",  # Only return required fields
        }

        try:
            # Make the search request
            response = requests.get(self._google_api_url, params=params)
            response.raise_for_status()
            search_results = response.json().get("items", [])

            # return None if no search results found
            if not search_results:
                logger.warning(
                    f"No ESG reports found for {self.company.security}. Returning None."
                )
                return None

            # format search results
            search_results = self._format_google_results(search_results)
        except HTTPError as e:
            logger.error(f"Failed to fetch search results: {e}. Exiting.")
            exit()

        return search_results

    @staticmethod
    def _format_google_results(search_results) -> list[SearchResult]:
        """Formats Google search results into a list of SearchResult objects.

        Args:
            search_results (list): A list of search results from the Google API.

        Returns:
            list[SearchResult]: A list of formatted search results.

        Example:
            >>> search = Search(company=Company(symbol="AAPL", security="Apple Inc."))
            >>> raw_results = [{"title": "Report 2023", "link": "http://example.com"}]
            >>> formatted_results = search._format_google_results(raw_results)
            >>> print(formatted_results)
            [SearchResult(title="Report 2023", link="http://example.com")]
        """
        formatted_results = []
        for result in search_results:
            logger.info(f"Search result: {result}")
            # Extract author and date from pagemap.metatags (if available)
            metatags = result.get("pagemap", {}).get("metatags", [{}])[0]

            # Extract relevant information from the search result metadata
            result = SearchResult(
                title=result.get("title"),
                metatag_title=metatags.get("title", None),
                author=metatags.get("author", None),
                link=result.get("link"),
                snippet=result.get("snippet"),
            )
            formatted_results.append(result)
        return formatted_results

    def sustainability_reports_dot_com(self) -> ESGReport:
        """Searches for sustainability reports on sustainabilityreports.com.

        Returns:
            ESGReport: An ESGReport object containing the report URL and year, or None if no report is found.

        Example:
            >>> search = Search(company=Company(symbol="AAPL", security="Apple Inc."))
            >>> report = search.sustainability_reports_dot_com()
            >>> if report.url:
            ...     print(f"Report URL: {report.url}, Year: {report.year}")
            ... else:
            ...     print("No report found.")
        """
        # strip company name
        company_name = self.company.symbol
        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 10)
        try:
            # Open the search page and enter the company name
            driver.get(self._sustainability_reports_url)
            search_box = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "input[name='search'][placeholder='Company Name or Ticker Symbol']",
                    )
                )
            )
            search_box.click()
            search_box.clear()
            search_box.send_keys(company_name)
            search_box.send_keys(Keys.ENTER)
            time.sleep(2)

            # wait for links to be clickable on results page
            all_links = wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            count = len(all_links)
            logger.debug(
                f"Number of <a> tags obtained using the original search term '{company_name}': {count}"
            )
            if count == 21:
                # Not enough tags on page, re-doing search with cleaned company name
                company_name = clean_company_name(company_name)
                logger.warning(
                    f"Original search term returned 21 <a> tags, re-searching using normalized search term '{company_name}'"
                )
                while True:
                    driver.get(self._sustainability_reports_url)
                    search_box = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                "input[name='search'][placeholder='Company Name or Ticker Symbol']",
                            )
                        )
                    )
                    search_box.click()
                    search_box.clear()
                    search_box.send_keys(company_name)
                    search_box.send_keys(Keys.ENTER)
                    time.sleep(2)
                    all_links = wait.until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
                    )
                    count = len(all_links)
                    logger.debug(
                        f"Number of <a> tags obtained using the normalized search term '{company_name}': {count}"
                    )
                    if count == 21:
                        if " " in company_name:
                            company_name = company_name.rsplit(" ", 1)[0]
                            logger.debug(
                                f"Still 21 <a> tags, shortening search term to: '{company_name}'"
                            )
                            continue
                        else:
                            logger.warning(
                                "Search term shortened to the minimum but still returns 21 <a> tags, returning none."
                            )
                            driver.quit()
                            return ESGReport(
                                url=None,
                                year=None,
                            )
                    else:
                        break
            elif count == 22:
                # If there are 22 <a> tags, the 11th one is the correct one.
                selected_link = all_links[10]
            elif count > 22:
                # If there are more than 22 <a> tags, we score the links to find the correct one.
                candidate_links = all_links[10 : count - 12 + 1]  # noqa: E203
                best_score = -1
                selected_link = None
                for link in candidate_links:
                    text = link.text.strip()
                    score = self._match_score(text, company_name)
                    if score > best_score:
                        best_score = score
                        selected_link = link
                if selected_link is None:
                    # If no link has a score better than -1, we select the first one.
                    selected_link = candidate_links[0]
            else:
                logger.warning("Not enough <a> tags on the page, cannot proceed.")
                driver.quit()
                return ESGReport(
                    url=None,
                    year=None,
                )

            # Click on the selected link and wait for the report link to appear.
            selected_link.click()
            time.sleep(2)
            try:
                report_link_element = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_form_10k"))
                )
            except TimeoutException:
                logger.warning(
                    "Link with class 'btn_form_10k' not found, returning none"
                )
                driver.quit()
                return ESGReport(
                    url=None,
                    year=None,
                )

            # Extract the report URL and the year from the link.
            report_url = report_link_element.get_attribute("href")
            logger.debug(f"Report URL: {report_url}")

            # Look for year in aria-label, link text, or href.
            aria_label = report_link_element.get_attribute("aria-label") or ""
            link_text = report_link_element.text or ""
            href = report_link_element.get_attribute("href") or ""

            report_year = None
            for text in [aria_label, link_text, href]:
                match_year = re.search(r"(20\d{2})", text)
                if match_year:
                    report_year = match_year.group(1)
                    break

            return ESGReport(
                url=report_url,
                year=report_year,
            )
        except Exception as e:
            logger.warning(f"Exception occurred: {e}. Returning None.")
            return ESGReport(
                url=None,
                year=None,
            )
        finally:
            time.sleep(5)
            driver.quit()

    @staticmethod
    def _match_score(text: str, search_term: str) -> int:
        """Calculates a match score between the text and the search term.

        Args:
            text (str): The text to match against.
            search_term (str): The search term to match.

        Returns:
            int: The match score (number of matching words).

        Example:
            >>> search = Search(company=Company(symbol="AAPL", security="Apple Inc."))
            >>> score = search._match_score("Apple Inc. Report 2023", "Apple Inc.")
            >>> print(score)
            2
        """
        text_words = set(text.lower().split())
        term_words = set(search_term.lower().split())
        return sum(1 for word in term_words if word in text_words)


if __name__ == "__main__":
    company = Company(
        symbol="AAPL",
        security="Apple Inc.",
        gics_sector="Technology",
        gics_industry="Technology",
        country="USA",
        region="North America",
    )

    search = Search(company=company)

    google_results = search.google()
    if google_results:
        logger.info(f"Found {len(google_results)} search results:")
        for result in google_results:
            logger.info(result)

    sustainability_reports_results = search.sustainability_reports_dot_com()
    logger.info(
        f"Result from SustainabilityReports.com: {sustainability_reports_results}"
    )

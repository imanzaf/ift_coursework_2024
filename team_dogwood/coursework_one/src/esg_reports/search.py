"""
Search class for scraping ESG reports from various sources.
"""

import os
import sys
import time
from datetime import datetime
from urllib.parse import quote

import requests
from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr
from requests.exceptions import HTTPError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from config.auth import auth_settings
from src.data_models.company import Company, SearchResult


class Search(BaseModel):
    """
    This class provides methods to search for and retrieve ESG (Environmental, Social, and Governance)
    reports for a given company using different sources:

    1. Google Custom Search API - searches for PDF ESG reports
    2. Sustainability Reports website - scrapes reports from responsibilityreports.com

    Args:
        company (Company): A Company object containing the company's metadata.
    """

    company: Company = Field(
        ..., description="The company to look for ESG reports for."
    )

    # Private attributes
    search_query: str = PrivateAttr(
        f"{company.security} {str(datetime.now().year)} ESG report filetype:pdf"
    )
    _encoded_search_query: str = PrivateAttr(quote(search_query))

    # Google API Config
    _google_api_url: str = PrivateAttr("https://www.googleapis.com/customsearch/v1")
    _google_api_key: str = PrivateAttr(auth_settings.GOOGLE_API_KEY)
    _google_engine_id: str = PrivateAttr(auth_settings.GOOGLE_ENGINE_ID)

    # Sustainability Reports URLs
    _sustainability_reports_url: str = PrivateAttr(
        "https://www.responsibilityreports.com"
    )
    _sustainability_reports_request_url: str = PrivateAttr(
        f"{_sustainability_reports_url}/Companies?search={company.security}"
    )

    def google(self):
        """
        Uses Google API to scrape search results.
        """
        params = {
            "q": self.search_query,
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
            search_results = self._format_search_results(search_results)
        except HTTPError as e:
            logger.error(f"Failed to fetch search results: {e}. Returning None.")
            return None

        return search_results

    @staticmethod
    def _format_search_results(search_results):
        """
        Cleans up search results to only keep relevant information.

        Args:
            search_results (list): A list of search results from the Google API.

        Returns:
            formatted_results (list[SearchResult]): list of parsed search results.
        """
        formatted_results = []
        for result in search_results:
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

    def sustainability_reports(self):
        """
        Uses Selenium to scrape ESG reports from the Sustainability Reports website.

        Returns:
            sustainability_reports (list[ESGReport]): A list of ESG reports for the company.
        """
        driver = webdriver.Chrome()
        try:
            driver.get(self._sustainability_reports_request_url)
            logger.debug("Opened page:", self._sustainability_reports_request_url)
            all_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            total_links = len(all_links)
            logger.debug(f"Found {total_links} <a> tags on the search results page.")
            if total_links < 11:
                logger.warning(
                    f"No results returned for {self.company.security}. Returning None."
                )
                return None

            company_details_page = all_links[10]
            company_details_page.click()
            logger.info("Found company details page. Waiting for page to load...")
            company_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )

            total_company_links = len(company_links)
            logger.debug(
                f"Found {total_company_links} <a> tags on the company details page."
            )
            needed_links = []
            if total_company_links > 15:
                needed_links.append(company_links[15])
            else:
                logger.warning(
                    "Not enough links (less than 16) on the company details page."
                )
                return None

            start_idx = 19
            end_idx = total_company_links - 12
            if end_idx >= start_idx:
                for idx in range(start_idx, end_idx + 1):
                    ordinal = idx + 1
                    if ordinal % 2 == 0:
                        needed_links.append(company_links[idx])
            else:
                logger.warning(
                    "Not enough links on the company details page to satisfy the range from the 20th link to the 12th from last link."
                )
                return None

            links = []
            if needed_links:
                for i, link in enumerate(needed_links):
                    text = link.text.strip()
                    href = link.get_attribute("href")
                    links.append({i: {"text": text, "href": href}})

                logger.info(f"Found {len(links)} links on the company details page.")
                logger.debug("Links:", links)
                return links
            else:
                logger.warning("No links found. Returning None.")
            return needed_links
        except Exception as e:
            logger.error("Exception occurred:", e)
        finally:
            time.sleep(5)
            driver.quit()


if __name__ == "__main__":
    company = Company(
        symbol="AAPL",
        security="Apple Inc.",
        gics_sector="Technology",
        gics_industry="Technology",
        country="USA",
        region="North America",
    )

    search = Search(company)

    google_results = search.google()
    if google_results:
        logger.info(f"Found {len(google_results)} search results:")
        for result in google_results:
            logger.info(result)

    # sustainability_reports_results = search.sustainability_reports()
    # if sustainability_reports_results:
    #     logger.info(f"Found {len(sustainability_reports_results)} sustainability reports:")
    #     for link in sustainability_reports_results:
    #         logger.info(link)

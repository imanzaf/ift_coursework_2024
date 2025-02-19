"""
TODO -
    - Methods for searching for URLs containing ESG reports of a specific company
        - maybe: google api, openai api, selenium + google search

TODO -
    - check what companies are included in https://github.com/trr266/srn_docs/blob/main/srn_docs_api.py
"""

import os
import sys
import time
from urllib.parse import quote

import requests
from loguru import logger
from requests.exceptions import HTTPError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from config.auth import auth_settings
from src.data_models.company import Company


class Search:

    def __init__(self, company: Company):
        self.company = company
        self.search_query = f"{self.company.security} latest ESG report filetype:pdf"
        self._encoded_search_query = quote(self.search_query)

        # Google API Config
        self._google_api_url = "https://www.googleapis.com/customsearch/v1"
        self._google_api_key = auth_settings.GOOGLE_API_KEY
        self._google_engine_id = auth_settings.GOOGLE_ENGINE_ID

        # Sustainability Reports URLs
        self._sustainability_reports_url = "https://www.responsibilityreports.com"
        self._sustainability_reports_request_url = f"{self._sustainability_reports_url}/Companies?search={self.company.security}"

    def google(self):
        """
        Uses Google API to scrape search results.
        """
        params = {
            "q": self.search_query,
            "key": self._google_api_key,
            "cx": self._google_engine_id,
        }

        try:
            # Make the search request
            response = requests.get(self._google_api_url, params=params)
            response.raise_for_status()
            search_results = response.json().get("items", [])[:3]

            if not search_results:
                logger.warning(
                    f"No ESG reports found for {self.company.security}. Returning None."
                )
                return None

            # format search results
            search_results = self._format_search_results(search_results)
            logger.info(f"search results: {search_results}")
        except HTTPError as e:
            logger.error(f"Failed to fetch search results: {e}. Returning None.")
            return None

        return search_results

    def _format_search_results(self, search_results):
        """
        Formats the search results into a list of dictionaries with relevant information.
        """
        formatted_results = []
        for result in search_results:
            metatags = result.get("pagemap", {}).get("metatags", [{}])[0]

            formatted_result = {
                "title": result.get("title"),
                "metatag_title": metatags.get("title"),
                "author": metatags.get("author"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
            }
            formatted_results.append(formatted_result)
        return formatted_results

    def sustainability_reports(self):
        """
        This is code that uses a web crawler and uses Apple as an example
        """
        driver = webdriver.Chrome()
        try:
            url = self._sustainability_reports_request_url
            driver.get(url)
            print("Opened page:", url)
            all_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            total_links = len(all_links)
            print(f"Found {total_links} <a> tags on the search results page.")
            if total_links < 11:
                print(
                    "Not enough links (less than 11) on the page to click the 11th link."
                )
                return
            eleventh_link = all_links[10]
            print(
                f"Clicking the 11th link: text='{eleventh_link.text.strip()}', URL={eleventh_link.get_attribute('href')}"
            )
            eleventh_link.click()
            print(
                "Clicked the 11th link, waiting for the company details page to load..."
            )
            company_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            total_company_links = len(company_links)
            print(f"Found {total_company_links} <a> tags on the company details page.")
            needed_links = []
            if total_company_links > 15:
                needed_links.append(company_links[15])
            else:
                print("Not enough links (less than 16) on the company details page.")
            start_idx = 19
            end_idx = total_company_links - 12
            if end_idx >= start_idx:
                for idx in range(start_idx, end_idx + 1):
                    ordinal = idx + 1
                    if ordinal % 2 == 0:
                        needed_links.append(company_links[idx])
            else:
                print(
                    "Not enough links on the company details page to satisfy the range from the 20th link to the 12th from last link."
                )
            if needed_links:
                print("The required filtered links are:")
                for i, link in enumerate(needed_links):
                    text = link.text.strip()
                    href = link.get_attribute("href")
                    print(f"  Link {i+1}: text='{text}', URL={href}")
            else:
                print("No links satisfy the conditions.")
            return needed_links
        except Exception as e:
            print("Exception occurred:", e)
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
        print(f"Found {len(google_results)} search results:")
        for result in google_results:
            print(result)

    sustainability_reports_results = search.sustainability_reports()
    if sustainability_reports_results:
        print(f"Found {len(sustainability_reports_results)} sustainability reports:")
        for link in sustainability_reports_results:
            print(link)

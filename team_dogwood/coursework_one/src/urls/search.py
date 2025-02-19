"""
TODO -
    - Methods for searching for URLs containing ESG reports of a specific company
        - maybe: google api, openai api, selenium + google search

TODO -
    - check what companies are included in https://github.com/trr266/srn_docs/blob/main/srn_docs_api.py
"""

import os
import re
import sys
import time
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger
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
        self.encoded_search_query = quote(self.search_query)

        # Google search URLs
        self._google_base_url = "https://www.google.com"
        self._google_request_url = (
            f"{self._google_base_url}/search?q={self.encoded_search_query}"
        )
        self._google_consent_url = "https://consent.google.com/save"

        # Google API Config
        self._google_api_url = "https://www.googleapis.com/customsearch/v1"
        self._google_api_key = auth_settings.GOOGLE_API_KEY
        self._google_engine_id = auth_settings.GOOGLE_ENGINE_ID

        # Sustainability Reports URLs
        self._sustainability_reports_url = "https://www.responsibilityreports.com"
        self._sustainability_reports_request_url = f"{self._sustainability_reports_url}/Companies?search={self.company.security}"

    @property
    def _user_agent(self):
        # update to get using selenium by accessing this site - https://httpbin.org/user-agent
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    def google_api(self):
        """
        Uses Google API to scrape search results.
        """
        params = {
            "q": self.search_query,
            "key": self._google_api_key,
            "cx": self._google_engine_id,
        }

        # Make the search request
        response = requests.get(self._google_api_url, params=params)
        response.raise_for_status()
        search_results = response.json().get("items", [])[:5]  # Get top 5 results

        if not search_results:
            logger.warning(f"No ESG reports found for {self.name}")
            # TODO - handle this case
            sys.exit()

        return search_results

    def google(self, retries=2):
        """
        Uses requests library to scrape Google search results.
        Note: not complete - stuck at redirect page (i think google is blocking the request due to automation)
        maybe try - https://rayobyte.com/blog/how-to-handle-captcha-in-selenium/
        """
        session = requests.Session()
        headers = {
            "User-Agent": self._user_agent,
        }
        session.headers.update(headers)
        tries = 0
        # runtime loop for the scrape
        while tries <= retries:
            try:
                response = session.get(
                    self._google_request_url, headers=headers, allow_redirects=True
                )
                print(response)

                # Check if Google returns a wait page
                if "if you are not redirected within a few seconds" in response.text:
                    print("Encountered a redirect page. Waiting...")
                    time.sleep(10)

                    # Extract the redirect URL
                    match = re.search(
                        r"If you're having trouble accessing Google Search, please<a href=\"(.*?)\">",
                        response.text,
                    )
                    if match:
                        redirect_url = "https://www.google.com" + match.group(1)
                        logger.info(f"Extracted redirect URL: {redirect_url}")

                    # Get the redirect page
                    response = session.get(redirect_url)

                    if not match:
                        # TODO - how to handle this?
                        pass

                # Check if the page contains a consent form
                if (
                    "consent.google.com" in response.url
                    or "Before you continue to Google" in response.text
                ):
                    logger.info("Google is asking for cookie consent. Accepting...")

                    form_data = {}
                    for match in re.finditer(
                        r'name="([^"]+)"\s+value="([^"]*)"', response.text
                    ):
                        form_data[match.group(1)] = match.group(2)

                    # Add the "Accept All" value (usually 'm' field)
                    form_data["m"] = "1"  # 1 = Accept all, 0 = Reject all
                    logger.info(f"Extracted form data: {form_data}")

                    # Send POST request to accept cookies
                    headers = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Referer": response.url,
                        "User-Agent": self._user_agent,
                    }

                    consent_response = session.post(
                        self._google_consent_url, data=form_data, headers=headers
                    )

                    logger.info(f"Consent response: {consent_response.status_code}")
                    if consent_response.status_code == 200:
                        print("Cookies accepted successfully.")

                results = []
                last_link = ""
                soup = BeautifulSoup(response.text, "html.parser")
                print(soup)
                index = 0
                for result in soup.find_all("div"):
                    title = result.find("h3")
                    print(title)
                    if title:
                        title = title.text
                    else:
                        continue
                    base_url = ""
                    link = result.find("a", href=True)
                    if link:
                        link = link["href"]
                        parsed_url = urlparse(link)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    else:
                        continue
                    # this is the full site info we wish to extract
                    site_info = {
                        "title": title,
                        "base_url": base_url,
                        "link": link,
                        "result_number": index,
                    }
                    if last_link != site_info["link"]:
                        results.append(result)
                # return our list of results
                print(f"Finished scrape with {tries} retries")
                return results
            except Exception:
                print("Failed to scrape the page")
                print("Retries left:", retries - tries)
                tries += 1
        # if this line executes, the scrape has failed
        raise Exception(f"Max retries exceeded: {retries}")

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

    google_results = search.google_api()
    if google_results:
        print(f"Found {len(google_results)} search results:")
        for result in google_results:
            print(result)

    # google_results = search.google()
    # if google_results:
    #     print(f"Found {len(google_results)} search results:")
    #     for link in google_results:
    #         print(link)

    # sustainability_reports_results = search.sustainability_reports()
    # if sustainability_reports_results:
    #     print(f"Found {len(sustainability_reports_results)} sustainability reports:")
    #     for link in sustainability_reports_results:
    #         print(link)

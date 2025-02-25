"""
TO DELETE!!!
only saved for reference of other methods we tried in case needed while developing
"""

import os
import re
import sys
import time
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

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

    @property
    def _user_agent(self):
        # update to get using selenium by accessing this site - https://httpbin.org/user-agent
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

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
        for link in google_results:
            print(link)

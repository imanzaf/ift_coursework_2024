import datetime as dt
import os
import re
import sys
from typing import List

import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

if not all([GOOGLE_API_KEY, SEARCH_ENGINE_ID]):
    raise ValueError("Environment variables GOOGLE_API_KEY, SEARCH_ENGINE_ID are not set.")


def _get_report_search_results(company_name: str, year: str) -> dict:
    """
    Retrieve the top 5 URLs of the company's ESG reports using Google Custom Search.
    """
    search_query = f"{company_name} {year} ESG report filetype:pdf"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_query,
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
    }

    # Make the search request
    response = requests.get(url, params=params)
    response.raise_for_status()
    search_results = response.json().get("items", [])[:5]  # Get top 5 results

    if not search_results:
        logger.warning(f"No ESG reports found for {company_name} in {year}")
        sys.exit()

    sorted_results = _sort_search_results(company_name, year, search_results)
    esg_urls = {
        index: value.get("link", "") for index, value in enumerate(sorted_results)
    }
    logger.debug(f"ESG report URLs for {company_name} in {year}: {esg_urls}")
    return esg_urls


def _sort_search_results(company_name: str, year: str, search_results: List[dict]) -> List[dict]:
    sorted_results = []
    for result in search_results:
        result_obj = SearchResult(
            company_name=company_name,
            url=result.get("link", ""),
            title=result.get("title", ""),
            description=result.get("snippet", ""),
            year=year
        )
        result["score"] = result_obj.score_search()

    sorted_results = sorted(
        search_results,
        key=lambda item: item.get("score"),
        reverse=True,
    )

    return sorted_results


class SearchResult:
    def __init__(self, company_name: str, url: str, title: str, description: str, year: str):
        self.company_name = company_name
        self.url = url
        self.title = title
        self.description = description
        self.year = year

    def score_search(self):
        stripped_name = self.company_name.split(" ")[0].lower()

        text_score = (
                self.score_text(self.title.lower())
                + self.score_text(self.description.lower())
                + (
                    -5
                    if (
                            stripped_name not in self.title.lower()
                            and stripped_name not in self.description.lower()
                            and stripped_name not in self.url.lower()
                    )
                    else 1
                )  # strongly penalize if name is not there
        )
        url_score = self.score_text(self.url) + (1 if self.company_name_lookup() else 0)
        year_score = self.score_year(
            self.title.lower() + self.description.lower() + self.url.lower()
        )

        # Validate the year in the metadata
        if self.year not in self.title.lower() and self.year not in self.description.lower():
            year_score -= 2  # penalize if the year is not found

        return text_score + url_score + year_score

    @staticmethod
    def score_text(text: str):
        # Score based on keywords matching
        keywords = ["esg", "sustainability", "report", "environmental", "social", "governance"]
        count = sum(keyword in text for keyword in keywords)
        return count

    def company_name_lookup(self):
        # get the site name from url
        url_index = re.search(
            r"(?:https?://)?(?:www\.)?([a-zA-Z0-9]+)", self.url
        ).group()
        stripped_name = self.company_name.split(" ")[0].lower()
        # check if company name starts with site name
        if stripped_name in url_index:
            return 2
        else:
            return 0

    @staticmethod
    def score_year(text):
        current_year = dt.datetime.now().year
        year_lag = current_year - 1
        two_year_lag = current_year - 2
        three_year_lag = current_year - 3

        # Extract all years from the text
        years_in_text = [int(year) for year in re.findall(r"\b\d{4}\b", text)]

        # Check for years that are 3 years older than the current year or older
        if any(year < three_year_lag for year in years_in_text):
            return -2

        # Check if the text contains the current year, year lag, or two-year lag
        if current_year in years_in_text:
            return 2
        if any(
                year in {current_year, year_lag, two_year_lag} for year in years_in_text
        ):
            return 1

        return -1


# Example usage:
if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    ticker = input("Enter the company ticker (optional): ").strip()  # Optional ticker input
    year = input("Enter the year for the ESG report: ")

    esg_urls = _get_report_search_results(company_name, year)

    # Display the correct link
    if esg_urls:
        print("\nFound ESG report links:")
        selected_url = None

        for index, url in esg_urls.items():
            print(f"{index + 1}. {url}")

            # Check if the URL contains the exact year provided by the user
            if year in url:
                # Also check if the ticker or company name is in the URL
                if (ticker.lower() in url.lower() or company_name.lower() in url.lower()):
                    selected_url = url
                    break  # Stop once we find the first URL that matches both year and name/ticker

        if not selected_url:
            print(f"\nNo data found for {company_name} in {year}")
        else:
            print(f"\nSelected ESG Report: {selected_url}")

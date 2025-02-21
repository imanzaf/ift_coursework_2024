import datetime as dt
import os
import re
import sys
from typing import List
import requests
from dotenv import load_dotenv
from loguru import logger
import itertools
import time

# Load environment variables
load_dotenv()

SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
# List of API keys (stored in .env file)
API_KEYS = [
    os.getenv("GOOGLE_API_KEY_1"),
    os.getenv("GOOGLE_API_KEY_2"),
    os.getenv("GOOGLE_API_KEY_3"),
    os.getenv("GOOGLE_API_KEY_4"),
    os.getenv("GOOGLE_API_KEY_5"),
    os.getenv("GOOGLE_API_KEY_6"),
    os.getenv("GOOGLE_API_KEY_7"),
    os.getenv("GOOGLE_API_KEY_8"),
    os.getenv("GOOGLE_API_KEY_9"),
    os.getenv("GOOGLE_API_KEY_10"),
    os.getenv("GOOGLE_API_KEY_11"),
    os.getenv("GOOGLE_API_KEY_12"),
    os.getenv("GOOGLE_API_KEY_13")
]



# Ensure all required environment variables are set
if not all(API_KEYS) or not SEARCH_ENGINE_ID:
    raise ValueError("Missing API keys or SEARCH_ENGINE_ID in environment variables.")

# Create an iterator to cycle through API keys
api_key_cycle = itertools.cycle(API_KEYS)

def get_current_api_key():
    """Get the next API key from the cycle"""
    return next(api_key_cycle)

def _get_report_search_results(company_name: str, ticker: str, year: str) -> str:
    """
    Retrieve the highest-scoring URL of the company's ESG report using Google Custom Search.
    Cycles through API keys if rate limits are hit.
    """
    search_query = f"{company_name} {year} ESG report filetype:pdf"
    url = "https://www.googleapis.com/customsearch/v1"

    # Try each API key until one succeeds
    for _ in range(len(API_KEYS)):
        api_key = get_current_api_key()  # Get the next API key
        params = {
            "q": search_query,
            "key": api_key,
            "cx": SEARCH_ENGINE_ID,
        }

        try:
            logger.info(f"Using API Key: {api_key}")
            response = requests.get(url, params=params)

            # Handle rate limit errors
            if response.status_code == 429:
                logger.warning(f"API Key {api_key} hit rate limit (429). Switching to next key...")
                time.sleep(2)  # Short delay before retrying
                continue  # Try the next API key

            response.raise_for_status()  # Raise exception for other errors

            search_results = response.json().get("items", [])[:5]  # Get top 5 results

            if not search_results:
                logger.warning(f"No ESG reports found for {company_name} ({ticker}) in {year}")
                return None
            for search_result in search_results:
                print(search_result.get("link", "No link available"))
            sorted_results = _sort_search_results(company_name, ticker, year, search_results)
            highest_scoring_url = sorted_results[0].get("link") if sorted_results else None
            logger.debug(f"Highest scoring ESG report URL for {company_name} in {year}: {highest_scoring_url}")
            return highest_scoring_url

        except requests.exceptions.RequestException as e:
            logger.error(f"Error with API Key {api_key}: {e}")
            time.sleep(2)  # Delay before retrying
            continue  # Try next API key

    # If all API keys fail
    logger.error("All API keys exhausted or failed. Please check API limits.")
    return None

def _sort_search_results(company_name: str, ticker: str, year: str, search_results: List[dict]) -> List[dict]:
    """
    Sort search results based on relevance to the company, ticker, and year.
    """
    for result in search_results:
        result_obj = SearchResult(
            company_name=company_name,
            ticker=ticker,
            url=result.get("link", ""),
            title=result.get("title", ""),
            description=result.get("snippet", ""),
            year=year
        )
        result["score"] = result_obj.score_search()

    sorted_results = sorted(search_results, key=lambda item: item.get("score"), reverse=True)
    return sorted_results

class SearchResult:
    def __init__(self, company_name: str, ticker: str, url: str, title: str, description: str, year: str):
        self.company_name = company_name
        self.ticker = ticker
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
                    -10
                    if (
                            stripped_name not in self.title.lower()
                            and stripped_name not in self.description.lower()
                            and stripped_name not in self.url.lower()
                    )
                    else 5
                )
        )
        if stripped_name in self.url.lower():
            text_score += 5

        year_score = self.score_year(
            self.title.lower() + self.description.lower() + self.url.lower(), self.year
        )

        if "sec/" in self.url.lower() or "sec-filings/" in self.url.lower():
            text_score -= 10
        if "10-k" or "8-k" in self.title.lower() or self.url.lower():
            text_score -= 5
        if "sustainability reports archive" in self.url.lower():
            text_score += 2

        return text_score + year_score

    @staticmethod
    def score_text(text: str):
        keywords = ["esg", "sustainability", "report", "environmental", "social", "governance"]
        return sum(keyword in text for keyword in keywords)

    def company_name_lookup(self):
        url_index = re.search(r"(?:https?://)?(?:www\.)?([a-zA-Z0-9]+)", self.url)
        url_index = url_index.group() if url_index else ""
        stripped_name = self.company_name.split(" ")[0].lower()
        return 2 if stripped_name in url_index else 0

    @staticmethod
    def score_year(text, target_year):
        years_in_text = [int(year) for year in re.findall(r"\b\d{4}\b", text)]
        penalty = sum(-3 for year in years_in_text if year != int(target_year))
        return (5 if int(target_year) in years_in_text else -5) + penalty

# Example usage
if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    ticker = input("Enter the company ticker (or leave blank): ")
    year = input("Enter the year for the ESG report: ")

    esg_url = _get_report_search_results(company_name, ticker, year)
    if esg_url:
        print(f"✅ Highest scoring ESG report URL: {esg_url}")
    else:
        print("❌ No valid ESG report found.")

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.esg_reports.search import Search


def test_format_google_search(google_response):
    formatted_response = Search._format_google_results(google_response)[0]
    assert formatted_response.title == "Apple ESG Report 2023"
    assert formatted_response.author == "Apple Inc."

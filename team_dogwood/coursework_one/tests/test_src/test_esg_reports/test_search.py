import os
import sys
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.esg_reports.search import Search


class TestGoogleSearch:

    def test_google_call(self, sample_company):
        with patch("requests.get") as mock_get:
            search = Search(company=sample_company)
            search.google()
            assert mock_get.assert_called_once

    def test_format_google_search(self, google_response):
        formatted_response = Search._format_google_results(google_response)[0]
        assert formatted_response.title == "Apple ESG Report 2023"
        assert formatted_response.author == "Apple Inc."

"""
TODO -
    - Methods for searching for URLs containing ESG reports of a specific company
        - maybe: google api, openai api, selenium + google search
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company


class Search:

    def __init__(self, company: Company):
        self.company = company

    def google(self):
        search_query = "+".join(  # noqa: F841
            f"{self.company.security} latest ESG report filetype:pdf".split()
        )
        # TODO - implement google search using selenium
        output = []
        return output


if __name__ == "__main__":
    company = Company(
        symbol="AAPL",
        security="Apple Inc.",
        gics_sector="Technology",
        gics_industry="Technology",
        country="USA",
        region="North America",
    )

    google_results = Search(company).google()

    print(google_results)

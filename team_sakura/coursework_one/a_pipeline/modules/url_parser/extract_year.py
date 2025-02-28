import re
from datetime import datetime


def extract_year_from_url_or_snippet(url: str, snippet: str) -> str:
    """
    Extracts the year from the given URL or snippet text, dynamically adapting to the current year.

    Args:
        url (str): The URL containing potential year information.
        snippet (str): The snippet text containing potential year information.

    Returns:
        str: Extracted year if found, otherwise "Unknown".
    """
    current_year = datetime.now().year

    # Regular expression to match years from 2000 up to the current year
    year_pattern = re.compile(rf"(20[0-2][0-{str(current_year)[-1]}])")

    url_match = year_pattern.search(url)
    snippet_match = year_pattern.search(snippet)

    if url_match:
        return url_match.group(1)
    if snippet_match:
        return snippet_match.group(1)

    return "Unknown"

import re
from datetime import datetime


def extract_year_from_url_or_snippet(url, snippet):
    """Extracts the year from the URL or snippet text, adapting to the current year."""
    current_year = datetime.now().year
    year_pattern = re.compile(
        rf"(20[0-2][0-{str(current_year)[-1]}])"
    )  # Matches years dynamically

    url_match = year_pattern.search(url)
    snippet_match = year_pattern.search(snippet)

    if url_match:
        return url_match.group(1)
    elif snippet_match:
        return snippet_match.group(1)

    return "Unknown"

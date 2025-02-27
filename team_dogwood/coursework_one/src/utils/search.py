import re

# Patterns for filtering legal suffixes and common articles
legal_pattern = (
    r"\b(Inc|Ltd|LLC|PLC|Corp|GmbH|S\.A|NV|AG|Pty Ltd|Co|Co\., Ltd|Pvt|Ltd)\b[.,\s]*"
)
article_pattern = r"\b(a|the|and|at|of)\b|\s&"


def clean_company_name(name: str) -> str:
    """Cleans a company name by removing legal suffixes, common articles, and extra spaces.

    This function removes common legal suffixes (e.g., "Inc", "Ltd", "LLC") and articles
    (e.g., "a", "the", "and") from the company name. It also strips any leading or trailing
    whitespace.

    Args:
        name (str): The raw company name to clean.

    Returns:
        str: The cleaned company name.

    Example:
        >>> raw_name = "Apple Inc. and The Company"
        >>> cleaned_name = clean_company_name(raw_name)
        >>> print(cleaned_name)
        "Apple Company"
    """
    # Remove legal suffixes
    cleaned_name = re.sub(legal_pattern, "", name, flags=re.IGNORECASE).strip()
    # Remove common articles and extra spaces
    cleaned_name = re.sub(
        article_pattern, "", cleaned_name, flags=re.IGNORECASE
    ).strip()
    return cleaned_name

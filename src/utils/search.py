import re

# patterns for filtering legal suffices and common articles etc.
legal_pattern = (
    r"\b(Inc|Ltd|LLC|PLC|Corp|GmbH|S\.A|NV|AG|Pty Ltd|Co|Co\., Ltd|Pvt|Ltd)\b[.,\s]*"
)
article_pattern = r"\b(a|the|and|at|of)\b|\s&"


def clean_company_name(name: str) -> str:
    """
    Clean the company name by removing legal suffixes, common articles, and extra spaces.
    """
    cleaned_name = re.sub(legal_pattern, "", name, flags=re.IGNORECASE).strip()
    cleaned_name = re.sub(
        article_pattern, "", cleaned_name, flags=re.IGNORECASE
    ).strip()
    return cleaned_name

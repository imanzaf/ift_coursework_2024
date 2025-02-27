import os
import urllib
from typing import List

from loguru import logger


def download_pdf_from_urls(urls: List[str], root_path: str):
    """Downloads PDF files from a list of URLs.

    This function attempts to download a PDF file from each URL in the list. It stops
    on the first successful download and returns the path to the downloaded file.
    If no URLs are successful, it logs an error and returns `None`.

    Args:
        urls (List[str]): A list of URLs to attempt downloading PDFs from.
        root_path (str): The directory path where the downloaded PDF will be saved.

    Returns:
        Union[str, None]: The path to the downloaded PDF file if successful, otherwise `None`.

    Example:
        >>> urls = [
        ...     "https://example.com/report.pdf",
        ...     "https://example.com/report",
        ... ]
        >>> root_path = "./downloads"
        >>> downloaded_file = download_pdf_from_urls(urls, root_path)
        >>> if downloaded_file:
        ...     print(f"Downloaded file: {downloaded_file}")
        ... else:
        ...     print("Failed to download any file.")
        Downloaded file: ./downloads/report.pdf
    """
    for url in urls:
        try:
            # Isolate PDF filename from URL
            pdf_file_name = (
                os.path.basename(url) + ".pdf"
                if not url.endswith(".pdf")
                else os.path.basename(url)
            )
            # Attempt to download the file
            with urllib.request.urlopen(url, timeout=15):
                urllib.request.urlretrieve(url, os.path.join(root_path, pdf_file_name))
            logger.info(f"Successfully downloaded {url} to {root_path}")
            return os.path.join(root_path, pdf_file_name)
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            continue

    logger.error("All URLs failed to download.")
    return None

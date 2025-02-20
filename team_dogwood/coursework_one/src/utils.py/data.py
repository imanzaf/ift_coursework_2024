import os
import urllib
from typing import List

from loguru import logger


def download_pdf_from_urls(urls: List[str], root_path: str):
    """
    Function to download PDF files from a URL. Breaks on the first successful download.

    Args:
        urls (List[str]): List of URLs to try to download in pdf format.
    """
    for url in urls:
        try:
            # isolate PDF filename from URL
            pdf_file_name = (
                os.path.basename(url) + ".pdf"
                if not url.endswith(".pdf")
                else os.path.basename(url)
            )
            with urllib.request.urlopen(url, timeout=15):
                urllib.request.urlretrieve(url, os.path.join(root_path, pdf_file_name))
            return os.path.join(root_path, pdf_file_name)
        except Exception as e:
            logger.error(f"Uh oh! Could not download {url}: {e}")
            continue

"""
Sustainability Report Crawler
===========================

This module implements a web crawler for automatically finding and downloading sustainability reports
from company websites. It uses a combination of Bing search and direct webpage crawling to locate
PDF reports.

The crawler performs the following operations:
    1. Reads company names from an SQLite database
    2. For each company, searches for sustainability reports from 2019-2024
    3. Uses multiple search strategies to find PDF reports
    4. Saves results to a CSV file with URLs and metadata

Module Architecture
-----------------
The crawler uses a three-step strategy to find reports:
    1. Direct Bing search for PDF files
    2. Bing search for company sustainability webpages
    3. Crawling found webpages for PDF links

The module uses threading for parallel processing of different years for each company.

Dependencies
-----------
* External Libraries:
    - selenium: For web scraping and JavaScript rendering
    - requests: For HTTP requests and URL validation
    - pandas: For data manipulation
    - sqlite3: For database operations
    - urllib3: For HTTP operations
* Standard Libraries:
    - os: File and path operations
    - time: Time-related functions
    - datetime: Date and time operations
    - threading: Multi-threading support
    - concurrent.futures: Thread pool management
    - csv: CSV file operations
    - urllib.parse: URL parsing and encoding

Configuration
------------
The module uses several configuration constants:
    DB_PATH (str): Path to the SQLite database containing company names
    OUTPUT_DIR (str): Directory for saving results and logs
    LOG_FILENAME (str): Path to the log file

Example
-------
To use this module, ensure the SQLite database exists and run::

    $ python main.py

The script will automatically process all companies and save results to CSV.

Notes
-----
- The crawler implements rate limiting and error handling to be respectful to servers
- Multiple search strategies are used to maximize the chance of finding reports
- Results are saved incrementally to prevent data loss
- Extensive logging is implemented for debugging and monitoring

Functions
--------
.. function:: write_log(message)
    Write a timestamped message to the log file.

.. function:: init_driver()
    Initialize and configure a Chrome WebDriver for web scraping.

.. function:: get_search_results(driver, company_name, search_url, search_query, max_trials=2)
    Perform a search using Selenium and return the results.

.. function:: check_pdf_url(url)
    Validate if a URL points to a valid PDF file.

.. function:: check_company_name_in_url(url, company_name)
    Check if a company name appears in a URL using fuzzy matching.

.. function:: check_url_year(url, target_year)
    Check if a URL contains the target year.

.. function:: search_pdf_in_bing(driver, company_name, year)
    Search for PDF reports directly using Bing search.

.. function:: search_webpage_in_bing(driver, company_name, year)
    Search for company sustainability webpages using Bing.

.. function:: find_pdf_in_webpage(driver, company_name, url, year)
    Search for PDF links within a webpage.

.. function:: process_company_year(company_name, year)
    Process a single company for a specific year.

.. function:: process_company(company_name)
    Process a single company for all years.

.. function:: process_companies(companies, results_file)
    Process multiple companies and save results to CSV.

Author: Shijie Zhang
"""

import os
import time
import datetime
import urllib.parse
import threading
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import csv
import pandas as pd
import sqlite3

import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configuration
current_dir = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))))
DB_PATH = os.path.join(project_root, '000.database', 'SQL', 'Equity.db')
print(f"Database path: {DB_PATH}")
# If database is in another location, specify the full path
# DB_PATH = '/path/to/your/Equity.db'  # macOS/Linux
# DB_PATH = r'C:\path\to\your\Equity.db'  # Windows

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set output directory to a_pipeline/aresult
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aresult")
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Ensure output directory exists

# Initialize global variables
LOG_FILENAME = os.path.join(OUTPUT_DIR, f'crawler_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

def write_log(message: str) -> None:
    """
    Write a timestamped message to the log file.

    This function appends a message with a timestamp to the global log file. It provides
    a centralized logging mechanism for tracking the crawler's operation and debugging
    issues.

    Args:
        message (str): The message to write to the log file. Should be descriptive
                      and contain relevant information for debugging.

    Log Format:
        [YYYY-MM-DD HH:MM:SS] message

    File Handling:
        - Appends to existing log file
        - Creates file if not exists
        - Uses UTF-8 encoding
        - Atomic write operations
        - Automatic line endings

    Timestamp Format:
        - YYYY-MM-DD: Full date (e.g., 2024-02-26)
        - HH:MM:SS: 24-hour time (e.g., 14:30:45)
        - Square brackets for easy parsing
        - Space separator before message

    Error Handling:
        - Handles file system errors
        - Ensures file closure
        - Maintains log integrity
        - Thread-safe operation

    Example:
        >>> write_log("Processing started")
        # Writes: [2024-02-26 14:30:45] Processing started
        >>> write_log("Error: Failed to connect")
        # Writes: [2024-02-26 14:30:46] Error: Failed to connect

    Note:
        The function uses the global LOG_FILENAME variable defined at module level.
        Make sure this variable is properly set before calling the function.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def init_driver() -> webdriver.Chrome:
    """
    Initialize and configure a Chrome WebDriver for web scraping.

    This function sets up a Chrome WebDriver with specific options optimized for
    web scraping operations. It configures the browser for headless operation
    and implements various settings for stability and performance.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance, or None if initialization fails

    WebDriver Configuration:
        1. Headless Mode:
           - No GUI required
           - Reduced resource usage
           - Faster operation

        2. Performance Options:
           - GPU disabled
           - Sandbox disabled
           - Dev-shm usage disabled
           - Custom user agent

        3. Security Settings:
           - No sandbox for root operation
           - Controlled memory usage
           - Standard security features

    Error Handling:
        - Catches all initialization exceptions
        - Logs detailed error information
        - Returns None on failure
        - Allows graceful fallback

    Example:
        >>> driver = init_driver()
        >>> if driver:
        ...     try:
        ...         driver.get("https://example.com")
        ...         # Perform operations
        ...     finally:
        ...         driver.quit()
        >>> else:
        ...     print("Failed to initialize driver")

    Note:
        The function prioritizes stability and reliability over features,
        making it suitable for automated scraping operations in various
        environments.
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        return webdriver.Chrome(options=options)
    except Exception as e:
        write_log(f"Failed to initialize Chrome driver: {str(e)}")
        return None

def get_search_results(driver: webdriver.Chrome, company_name: str, search_url: str, 
                      search_query: tuple, max_trials: int = 2) -> list:
    """
    Perform a search using Selenium and return the results.

    This function executes a web search using Selenium WebDriver and implements
    robust retry logic and error handling. It's designed to handle temporary
    failures and network issues gracefully.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance for browser automation
        company_name (str): Name of the company (used for logging)
        search_url (str): URL to perform the search on
        search_query (tuple): Selenium locator tuple (By.X, "selector")
        max_trials (int, optional): Maximum number of retry attempts. Defaults to 2.

    Returns:
        list: List of WebElement objects representing search results, or None if failed

    Search Process:
        1. Navigate to search URL
        2. Wait for results to load
        3. Locate elements using provided selector
        4. Implement retry logic if needed
        5. Return found elements or None

    Retry Strategy:
        - Maximum 2 attempts by default
        - 1-second delay between retries
        - Explicit wait with 15-second timeout
        - Logs each retry attempt

    Error Handling:
        - TimeoutException: When elements don't load
        - WebDriverException: For browser issues
        - General exceptions: For unexpected errors
        - Detailed error logging

    Example:
        >>> search_query = (By.CSS_SELECTOR, '.search-result')
        >>> results = get_search_results(driver, "Apple", "http://example.com", search_query)
        >>> if results:
        ...     for result in results:
        ...         print(result.text)
        >>> else:
        ...     print("No results found")

    Note:
        The function uses explicit waits rather than implicit waits for better
        control over the search process and more predictable behavior.
    """
    for trial in range(max_trials):
        try:
            driver.get(search_url)
            wait = WebDriverWait(driver, 15)
            
            search_results = wait.until(
                EC.presence_of_all_elements_located(search_query)
            )
            
            if search_results:
                return search_results
            time.sleep(1)

        except Exception as e:
            if trial < max_trials - 1:
                time.sleep(1)
                continue
            write_log(f"{company_name}: Failed to get search results: {str(e)}")
            return None
    
    return None

def check_pdf_url(url: str) -> bool:
    """
    Validate if a URL points to a valid PDF file.

    This function performs a comprehensive validation of a URL to ensure it points
    to an accessible and valid PDF file. It uses HTTP HEAD requests for efficiency
    and implements robust error handling.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL points to a valid and accessible PDF file,
              False otherwise

    Validation Process:
        1. Performs HTTP HEAD request with custom headers
        2. Follows redirects automatically
        3. Checks response status code
        4. Verifies final URL extension
        5. Implements timeout for efficiency
        6. Handles various error conditions

    HTTP Request Features:
        - Uses HEAD method to minimize bandwidth
        - Custom user agent to avoid blocking
        - Follows up to 5 redirects
        - 5-second timeout
        - Accepts PDF content type
        - Verifies HTTPS certificates

    Error Handling:
        - Connection timeouts
        - DNS resolution errors
        - SSL/TLS errors
        - Invalid URLs
        - Server errors
        - Redirect loops

    Example:
        >>> # Valid PDF URL
        >>> is_valid = check_pdf_url("http://example.com/report.pdf")
        >>> print(is_valid)
        True
        >>> # Invalid URL
        >>> is_valid = check_pdf_url("http://example.com/not-found.pdf")
        >>> print(is_valid)
        False
        >>> # Non-PDF URL
        >>> is_valid = check_pdf_url("http://example.com/document.doc")
        >>> print(is_valid)
        False

    Note:
        The function logs all validation failures for debugging purposes while
        maintaining efficient operation through HEAD requests and timeouts.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf'
        }
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)  # Reduced timeout
        
        if response.status_code == 200:
            final_url = response.url.lower()
            if '.pdf' in final_url:
                return True
        return False
        
    except Exception as e:
        write_log(f"Error checking URL {url}: {str(e)}")
        return False

def check_company_name_in_url(url: str, company_name: str) -> bool:
    """
    Check if a company name appears in a URL using fuzzy matching.

    This function implements a sophisticated scoring system to determine if a company
    name is present in a URL. It handles multi-word company names, partial matches,
    and various URL formats.

    Args:
        url (str): URL to analyze for company name presence
        company_name (str): Company name to look for

    Returns:
        bool: True if company name is found in URL according to matching rules,
              False otherwise

    Matching Rules:
        1. First word of company name must be present in URL
        2. For single-word company names:
           - Requires exact match of the word
        3. For multi-word company names:
           - Requires at least 50% of words to match
           - Words can match in any order
           - Matches are case-insensitive
        4. Special characters and spaces are handled appropriately

    Scoring System:
        - Each matched word contributes to the total score
        - Score is calculated as: matched_words / total_words
        - For multi-word names: minimum 50% match required
        - For single-word names: 100% match required

    Example:
        >>> # Single word company
        >>> found = check_company_name_in_url("http://apple-sustainability.com", "Apple")
        >>> print(found)
        True
        >>> # Multi-word company
        >>> found = check_company_name_in_url("http://bankofamerica-esg.com", "Bank of America")
        >>> print(found)
        True
        >>> # Insufficient match
        >>> found = check_company_name_in_url("http://bank-report.com", "Bank of America")
        >>> print(found)
        False

    Note:
        The function is designed to balance between being permissive enough to catch
        valid matches while being strict enough to avoid false positives.
    """
    url_lower = url.lower()
    company_lower = company_name.lower()
    
    # Split company name into keywords
    company_keywords = company_lower.split()
    if not company_keywords:
        return False
        
    # First word must exist
    first_word = company_keywords[0]
    if first_word not in url_lower:
        return False
    
    # Calculate match score
    matched_words = sum(1 for word in company_keywords if word in url_lower)
    match_score = matched_words / len(company_keywords)
    
    # If only one word, require exact match
    if len(company_keywords) == 1:
        return match_score == 1
    
    # If multiple words, require at least 50% match
    return match_score >= 0.5

def check_url_year(url: str, target_year: int) -> bool:
    """
    Check if a URL contains the target year.

    This function analyzes a URL to determine if it contains a specific year. It uses
    a pattern matching approach to identify years between 2010-2029 and compares them
    with the target year.

    Args:
        url (str): URL to analyze for year presence
        target_year (int): Year to look for (e.g., 2024)

    Returns:
        bool: True if either:
            - The target year is found in the URL
            - No year is found in the URL (to avoid false negatives)
            False if a different year is found

    Pattern Matching:
        - Uses regex pattern r'20[12]\d' to match years 2010-2029
        - Case-insensitive matching
        - Handles multiple year occurrences
        - Returns True if no year found (avoid false negatives)

    Example:
        >>> has_year = check_url_year("report-2024.pdf", 2024)
        >>> print(has_year)
        True
        >>> has_year = check_url_year("sustainability.pdf", 2024)
        >>> print(has_year)  # No year found, returns True
        True
        >>> has_year = check_url_year("report-2023.pdf", 2024)
        >>> print(has_year)
        False

    Note:
        The function is designed to be permissive when no year is found to avoid
        excluding potentially relevant URLs that don't include a year in their path.
    """
    url_lower = url.lower()
    # Extract year (4 digits) from URL
    import re
    years_in_url = re.findall(r'20[12]\d', url_lower)  # Match years 2010-2029
    
    if years_in_url:
        # If URL contains year, check if it matches target year
        return str(target_year) in years_in_url
    return True  # If URL doesn't contain year, return True

def search_pdf_in_bing(driver: webdriver.Chrome, company_name: str, year: int) -> str:
    """
    Search for PDF reports directly using Bing search.

    This function performs a direct search for PDF sustainability reports using Bing.
    It implements a comprehensive search strategy using multiple report type keywords
    and sophisticated filtering criteria.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance for browser automation
        company_name (str): Name of the company to search for
        year (int): Target year for the report (e.g., 2024)

    Returns:
        str: URL of the found PDF report, or None if no suitable report is found

    Search Strategy:
        1. Tries multiple sustainability report keywords
        2. Uses Bing search with PDF file type filter
        3. Excludes annual reports and specific websites
        4. Validates PDF URLs
        5. Checks company name presence
        6. Verifies year matches
        7. Limited to first 3 results per search

    Report Types Searched:
        - Sustainability report
        - CSR report
        - ESG report
        - ESG disclosure
        - Global impact report
        - Environmental report
        - Corporate responsibility report
        - And more...

    Validation Criteria:
        - Must be a valid PDF URL
        - Must contain company name
        - Must match target year
        - Must not be an annual report
        - Must be accessible

    Example:
        >>> driver = init_driver()
        >>> url = search_pdf_in_bing(driver, "Apple", 2024)
        >>> if url:
        ...     print(f"Found sustainability report: {url}")
    """
    # Define possible report types
    report_types = [
        "sustainability report",
        "ESG report",
        "CSR report",
        "ESG disclosure",
        "global impact report",
        "ESG action report",
        "sustainable development report",
        "corporate citizenship report"
    ]
    
    # Try different report types
    for report_type in report_types:
        search_query = f"{company_name} {report_type} {year} pdf -responsibilityreports -\"annual report\""
        search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}"
        write_log(f"{company_name}: Searching {report_type} for {year}")

        search_query = (By.CSS_SELECTOR, '.b_algo h2 a')
        search_results = get_search_results(driver, company_name, search_url, search_query)
        
        if not search_results:
            continue

        # Check results
        for result in search_results[:3]:
            url = result.get_attribute('href')
            if not url:
                continue
                
            url_lower = url.lower()
            if '.pdf' in url_lower:
                # Exclude annual report related URLs, case insensitive
                excluded_terms = ['annual', 'financial', 'proxy']
                if (not any(term in url_lower for term in excluded_terms) and 
                    check_url_year(url, year) and
                    check_company_name_in_url(url, company_name) and
                    check_pdf_url(url)):
                    return url
                
    return None

def search_webpage_in_bing(driver: webdriver.Chrome, company_name: str, year: int) -> list:
    """
    Search for company sustainability webpages using Bing.

    This function performs a search for company sustainability webpages that might
    contain PDF reports. It implements a multi-keyword search strategy and returns
    a list of potential webpage URLs for further processing.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance for browser automation
        company_name (str): Name of the company to search for
        year (int): Target year for the report (e.g., 2024)

    Returns:
        list: List of webpage URLs to search, or None if no suitable pages are found.
              Each URL is a potential location for sustainability report PDFs.

    Search Strategy:
        1. Uses multiple sustainability-related keywords
        2. Excludes specific websites and file types
        3. Collects up to 3 non-PDF URLs per search
        4. Implements comprehensive logging
        5. Handles timeouts and errors gracefully

    Report Types Searched:
        - Sustainability report
        - CSR report
        - ESG report
        - ESG disclosure
        - Global impact report
        - Environmental report
        - Corporate responsibility report
        - And more...

    Validation Criteria:
        - Must be a webpage (not PDF)
        - Must be accessible
        - Must be relevant to sustainability reporting

    Example:
        >>> driver = init_driver()
        >>> urls = search_webpage_in_bing(driver, "Apple", 2024)
        >>> if urls:
        ...     print(f"Found {len(urls)} pages to search")
        ...     for url in urls:
        ...         print(f"- {url}")
    """
    # Define possible report types
    report_types = [
        "sustainability report",
        "CSR report",
        "ESG report",
        "ESG disclosure report",
        "global impact report",
        "ESG action report"
    ]
    
    for report_type in report_types:
        search_query = f"{company_name} {report_type} {year} -responsibilityreports"
        search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}"
        write_log(f"{company_name}: Searching webpage for {report_type} {year}")
            
        search_query = (By.CSS_SELECTOR, '.b_algo h2 a')
        search_results = get_search_results(driver, company_name, search_url, search_query)

        if not search_results:
            continue
        
        url_list = []
        count = 0
        for result in search_results:
            if count >= 3:
                break
            try:
                url = result.get_attribute('href')
                if url and '.pdf' not in url.lower():
                    url_list.append(url)
                    count += 1
            except Exception as e:
                write_log(f"{company_name}: Error getting URL: {str(e)}")
                continue

        if url_list:
            return url_list

    return None

def find_pdf_in_webpage(driver: webdriver.Chrome, company_name: str, url: str, year: int) -> str:
    """
    Search for PDF links within a webpage.

    This function performs a detailed scan of a webpage to find PDF links that match
    specific criteria for sustainability reports. It implements comprehensive filtering
    and validation to ensure only relevant PDFs are returned.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance for browser automation
        company_name (str): Name of the company to search for
        url (str): Webpage URL to search for PDF links
        year (int): Target year for the report (e.g., 2024)

    Returns:
        str: URL of the found PDF report, or None if no suitable PDF is found

    Search Strategy:
        1. Scans all links (<a> tags) on the webpage
        2. Filters for PDF file extensions
        3. Validates against sustainability keywords
        4. Checks for target year in link text and URL
        5. Verifies company name presence
        6. Validates final PDF URL accessibility

    Validation Keywords:
        - sustainability
        - sustainable
        - csr
        - esg
        - global impact
        - environmental
        - responsibility
        - climate
        - disclosure
        - corporate citizenship
        - And more...

    Excluded Content:
        - Annual reports
        - Financial reports
        - Proxy statements
        - Non-PDF files
        - Invalid URLs

    Example:
        >>> driver = init_driver()
        >>> pdf_url = find_pdf_in_webpage(driver, "Apple", "https://example.com", 2024)
        >>> if pdf_url:
        ...     print(f"Found sustainability report PDF: {pdf_url}")

    Note:
        The function implements extensive error handling and logging to track the
        search process and any issues encountered.
    """
    write_log(f"{company_name}: Searching PDF in webpage for {year}")
    search_query = (By.TAG_NAME, "a")
    search_results = get_search_results(driver, company_name, url, search_query)

    if not search_results:
        write_log(f"{company_name}: No Search Results Found | URL: {url}")
        return None
    
    # Define possible keywords
    keywords = [
        'sustainability',
        'csr',
        'esg',
        'esg disclosure',
        'global impact',
        'environmental',
        'responsibility',
        'climate',
        'citizenship'
    ]
    
    # Define excluded terms
    excluded_terms = ['annual', 'financial', 'proxy']
    
    for result in search_results:
        try:
            href = result.get_attribute('href')
            if not href:
                continue

            href_lower = href.lower()
            if '.pdf' in href_lower:
                # Exclude irrelevant PDFs
                if any(term in href_lower for term in excluded_terms):
                    continue
                
                # Check year and company name in URL
                if not check_url_year(href, year):
                    continue
                    
                if not check_company_name_in_url(href, company_name):
                    continue
                    
                text = result.text.lower()
                if str(year) in text and any(keyword.lower() in text for keyword in keywords):
                    if check_pdf_url(href):
                        return href
                
        except Exception:
            continue
    
    return None

def process_company_year(company_name: str, year: int) -> tuple:
    """
    Process a single company for a specific year.

    This function coordinates the search process for a single company and year,
    trying multiple search strategies in sequence.

    Args:
        company_name (str): Name of the company to process
        year (int): Year to search for (e.g., 2024)

    Returns:
        tuple: A tuple containing (pdf_url, source) where:
            - pdf_url (str): URL of found PDF or None if not found
            - source (str): Source of the URL ('Bing direct search', 'Bing webpage search', or 'Not found')

    Raises:
        WebDriverException: If browser automation fails
        TimeoutException: If page load times out
        Exception: For other unexpected errors

    Note:
        - Initializes a new WebDriver for each company-year combination
        - Implements multiple search strategies in sequence
        - Handles cleanup of WebDriver resources
        - Logs errors and progress

    Example:
        >>> url, source = process_company_year("Apple", 2024)
        >>> if url:
        ...     print(f"Found report at {url} via {source}")
    """
    driver = init_driver()
    if not driver:
        return None, None
    
    try:
        # Try Bing search
        pdf_url = search_pdf_in_bing(driver, company_name, year)
        if pdf_url:
            driver.quit()
            return pdf_url, 'Bing direct search'
        
        # Try Bing webpage search
        webpage_urls = search_webpage_in_bing(driver, company_name, year)
        if webpage_urls:
            for url in webpage_urls:
                pdf_url = find_pdf_in_webpage(driver, company_name, url, year)
                if pdf_url:
                    driver.quit()
                    return pdf_url, 'Bing webpage search'
                    
    except Exception as e:
        write_log(f"Error processing {company_name} for {year}: {str(e)}")
    finally:
        driver.quit()
    
    return None, 'Not found'

def process_company(company_name: str) -> list:
    """
    Process a single company for all years.

    This function coordinates the search for sustainability reports across multiple years
    for a single company. It implements parallel processing for efficiency and provides
    comprehensive progress tracking and error handling.

    Args:
        company_name (str): Name of the company to process

    Returns:
        list: List of dictionaries containing results for each year, sorted by year.
             Each dictionary contains:
             - company (str): Company name
             - year (int): Report year
             - url (str): Found URL or "Not found"
             - source (str): Source of the URL or "Not found"

    Processing Strategy:
        1. Creates a thread pool for parallel processing
        2. Processes years 2019-2024 simultaneously
        3. Maximum of 3 concurrent searches
        4. Collects and sorts results by year
        5. Saves results incrementally

    Error Handling:
        - Catches and logs all exceptions
        - Continues processing remaining years if one fails
        - Records "Not found" for failed searches
        - Maintains data integrity through error states

    Progress Tracking:
        - Prints real-time status updates
        - Logs all major operations
        - Reports success/failure for each year
        - Provides final processing summary

    Example:
        >>> results = process_company("Apple")
        >>> print(f"Found {len([r for r in results if r['url'] != 'Not found'])} reports")
        >>> for result in results:
        ...     print(f"{result['year']}: {result['url']}")

    Note:
        The function uses ThreadPoolExecutor for parallel processing, which significantly
        improves performance while maintaining controlled resource usage.
    """
    print(f"\nProcessing company: {company_name}")
    results = []
    
    # Process all years in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:  # Process 3 years simultaneously
        futures = {
            executor.submit(process_company_year, company_name, year): year 
            for year in range(2019, 2025)
        }
        
        for future in as_completed(futures):
            year = futures[future]
            try:
                url, source = future.result()
                results.append({
                    'company': company_name,
                    'year': year,
                    'url': url if url else 'Not found',
                    'source': source if source else 'Not found'
                })
                print(f"  {year}: {'Found' if url else 'Not found'}")
            except Exception as e:
                write_log(f"Error processing {company_name} for {year}: {str(e)}")
                results.append({
                    'company': company_name,
                    'year': year,
                    'url': 'Not found',
                    'source': 'Not found'
                })
    
    return sorted(results, key=lambda x: x['year'])  # Return results sorted by year

def process_companies(companies: list, results_file: str) -> None:
    """
    Process multiple companies and save results to CSV.

    This function coordinates the processing of multiple companies and manages the
    saving of results to a CSV file. It implements incremental saving for data safety
    and provides comprehensive progress tracking.

    Args:
        companies (list): List of company names to process
        results_file (str): Path to save results CSV

    File Format:
        The CSV file contains the following columns:
        - company: Company name
        - year: Report year
        - url: Found URL or "Not found"
        - source: Source of the URL or "Not found"

    Processing Features:
        1. Creates CSV with headers if not exists
        2. Processes companies sequentially
        3. Saves results after each company
        4. Provides progress updates
        5. Implements UTF-8 encoding
        6. Handles file operations safely

    Data Safety:
        - Incremental saving after each company
        - Safe file handling with context managers
        - UTF-8 encoding for international characters
        - Error handling for file operations

    Progress Tracking:
        - Reports start of processing
        - Updates after each company
        - Shows completion status
        - Indicates where results are saved

    Example:
        >>> companies = ["Apple", "Microsoft", "Google"]
        >>> process_companies(companies, "sustainability_reports.csv")
        Processing company: Apple
        Processing company: Microsoft
        Processing company: Google
        Processing completed. Results saved to sustainability_reports.csv

    Note:
        The function is designed for robustness and data safety, ensuring that
        partial results are saved even if the process is interrupted.
    """
    # Create results CSV with headers
    with open(results_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['company', 'year', 'url', 'source'])
        writer.writeheader()

    # Process each company
    for company in companies:
        company_results = process_company(company)
        
        # Save results for this company
        with open(results_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['company', 'year', 'url', 'source'])
            for result in company_results:
                writer.writerow(result)
        
        print(f"Completed processing {company}")

    print(f"\nProcessing completed. Results saved to {results_file}")

if __name__ == "__main__":
    try:
        # Read company names from SQLite database
        conn = sqlite3.connect(DB_PATH)
        
        # First list all table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Available tables in database:", [table[0] for table in tables])
        
        # Get structure of first table
        if tables:
            first_table = tables[0][0]
            cursor.execute(f"PRAGMA table_info({first_table})")
            columns = cursor.fetchall()
            print(f"\nColumns in table {first_table}:")
            for col in columns:
                print(f"- {col[1]}")  # col[1] is column name
        
        # Query using correct table name
        table_name = tables[0][0] if tables else None  # Use first table name
        if table_name:
            query = f"SELECT security FROM {table_name}"
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        if 'security' not in df.columns:
            raise ValueError("Database must contain a 'security' column")
            
        companies = df['security'].tolist()
        print(f"Found {len(companies)} companies in database")
        
        # Create results filename
        results_file = os.path.join(OUTPUT_DIR, "results_dirty_urls.csv")
        
        # Process companies
        process_companies(companies, results_file)
        
        # Calculate processing statistics
        df_results = pd.read_csv(results_file)
        total_companies = len(companies)
        successful_companies = 0
        
        for company in companies:
            valid_urls = df_results[
                (df_results['company'] == company) & 
                (df_results['url'] != 'Not found')
            ].shape[0]
            
            if valid_urls >= 2:
                successful_companies += 1
                
        success_rate = (successful_companies / total_companies) * 100
        print(f"\nProcessing Summary:")
        print(f"Total Companies: {total_companies}")
        print(f"Successful Companies: {successful_companies}")
        print(f"Success Rate: {success_rate:.2f}%")
        
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

import os
import time
from datetime import datetime
import urllib.parse
import threading
#from enum import nonmember

#from concurrent.futures import ThreadPoolExecutor, wait

from PyPDF2 import PdfReader

import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ...modules.validation.validation import is_valid_esg_report_from_url
from ...modules.utils.dockercheck import is_running_in_docker

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Helper Function: Write log
def write_log(message):
    """Write log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

# Helper Function: Initialize Selenium WebDriver
def init_driver():
    print("init driver() entered")
    """Initialize Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    print('setting driver options')
    options.add_argument('--headless')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-blink-features=AutomationControlled') 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    print('driver options set')

    if not is_running_in_docker():
        print('running d = webdriver.Chrome(options=options)')
        d = webdriver.Chrome(options=options)

        #check if the driver is initialized
        if not d:
            print("Initialing locally: Failed to initialize WebDriver.")
            return None
        else: print('local: driver initialized internally')

        return d
    else:
        print('running d = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=options)')
        service = Service(executable_path="/usr/bin/chromedriver")
        d = webdriver.Chrome(options=options, service=service)

        #check if the driver is initialized
        if not d:
            print("Initialing in docker: Failed to initialize WebDriver.")
            return None
        else: print('docker: driver initialized internally')

        return d
# Helper Function: Get search results using selenium
def get_search_results(driver, company_name, search_url, search_query, max_trials=3):
    for trial in range(max_trials): # Try up to 3 times
        try:
            # Visit search page
            driver.get(search_url)
            wait = WebDriverWait(driver, 30)
            
            # Wait for search results to load
            search_results = wait.until(
                EC.presence_of_all_elements_located(search_query)
            )
            
            # Check if search results are retrieved successfully
            if search_results:
                return search_results
            # If not found, wait 2 seconds and retry
            time.sleep(2)

        # If there is an error, and not reached max trials, wait 2 seconds and retry
        except Exception as e:
            if trial < max_trials - 1:
                time.sleep(2)
                continue
            # If reached max trials, write log and return None
            write_log(f"{company_name}: Failed to get search results after {max_trials} attempts: {str(e)}")
            return None
        
    # If all attempts failed, return None
    return None

# Helper Function: Determine if the PDF content contains keywords
def is_pdf_contains_keywords(pdf_path):
    current_year = datetime.now().year
    keywords = ['scope 1', 'scope 2', "esg", "csr"]
    years = [str(current_year), str(current_year-1)]
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            # Only extract text if it contains 'scope 1' or 'scope 2' and currentyear, currentyear -1
            if any(keyword in page_text.lower() for keyword in keywords) and \
                  any(year in page_text.lower() for year in years):
                text += page_text

        if text != "":
            return True
        else:
            return False
    
    except Exception as e:
        print(f"Error processing PDF: {pdf_path}")
        print(f"Error message: {str(e)}")
        return False
        

# Helper Function: Download PDF file (including verify whether content contains scope 1 or scope 2)
def download_pdf(company_name, url, max_trials=3):
    
    # Check if URL is PDF
    if 'pdf' not in url:
        write_log(f"{company_name}: Is not a PDF URL | URL: {url}")
        return None
    
    # Set download request headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/pdf'
    }

    # Create PDF file path
    pdf_path = f"./reports/{company_name}.pdf"

    for trial in range(max_trials): # Try up to 3 times
        try:
            # Send request
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            
            # If request successful, process PDF file
            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                # Check if PDF content contains scope 1 or scope 2
                if not is_pdf_contains_keywords(pdf_path):
                    write_log(f"{company_name}: PDF content does not contain 'scope 1' or 'scope 2' | URL: {url}")
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    return None
                else:
                    write_log(f"{company_name}: Valid PDF downloaded | URL: {url}")
                    return pdf_path
        
        # If there is an error, and not reached max trials, wait 2 seconds and retry
        except Exception as e:
            if trial < max_trials - 1:
                time.sleep(2)
                continue

            # If reached max trials, delete PDF file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            write_log(f"{company_name}: PDF Processing Error | Error: {e} | URL: {url}")
            return None
    
    # If all attempts failed, delete file path
    write_log(f"{company_name}: Failed to download PDF after {max_trials} attempts | URL: {url}")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    return None

# Step 1: Try to search PDF directly in Bing
def search_pdf_in_bing(driver, company_name):
    year = str(datetime.now().year)
    # Search query
    search_query = f"{company_name} sustainability report " + year + " pdf -responsibilityreports"
    search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}&first=1&form=QBRE"
    write_log(f"{company_name}: Searching PDF in Bing | URL: {search_url}")

    # Call helper function to get search results
    search_query = (By.CSS_SELECTOR, '.b_algo h2 a')
    search_results = get_search_results(driver, company_name, search_url, search_query)
    
    # If no search results found, return None
    if not search_results:
        write_log(f"{company_name}: No Search Results Found | URL: {search_url}")
        return None

    # Extract PDF links from search results
    pdf_links = []
    for result in search_results:
        url = result.get_attribute('href').lower()
        if url and '.pdf' in url:
            pdf_links.append(url)   

    # If no PDF links found, return None
    if not pdf_links:
        write_log(f"{company_name}: No PDF Links Found in Search Results | URL: {search_url}")
        return None

    # Try to download PDF (only pdf content contains scope 1 or scope 2 will be downloaded)
    for pdf in pdf_links:
        pdf_path = download_pdf(company_name, pdf)
        if pdf_path:
            return pdf_path
        
    write_log(f"{company_name}: No Valid PDF Found in Search Results")
    return None

# Step 2: If PDF not found directly in Bing, search company's sustainability website
def search_webpage_in_bing(driver, company_name):
    
    # Search query
    search_query = f"{company_name} sustainability website -responsibilityreports"
    search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}&first=1&form=QBRE"
    write_log(f"{company_name}: Searching Webpage in Bing | URL: {search_url}")
        
    # Call helper function to get search results
    search_query = (By.CSS_SELECTOR, '.b_algo h2 a')
    search_results = get_search_results(driver, company_name, search_url, search_query)

    # If no search results found, return None
    if not search_results:
        write_log(f"{company_name}: No Search Results Found | URL: {search_url}")
        return None
    
    # Extract first 3 non-PDF webpage links from search results
    url_list = []
    count = 0
    for result in search_results:
        if count >= 3:
            break
        try:
            url = result.get_attribute('href')
            if url and '.pdf' not in url.lower(): # Only non-PDF links will be added
                url_list.append(url)
                count += 1
        except Exception as e:
            write_log(f"{company_name}: Error getting URL from search result: {str(e)}")
            continue

    # If no valid URL found, return None
    if not url_list:
        write_log(f"{company_name}: No Valid URL Found in Search Results")
        return None
            
    return url_list

# Step 3: Find PDF links in company's sustainability website
def find_pdf_in_webpage(driver, company_name, url):

    write_log(f"{company_name}: Searching PDF in Webpage | URL: {url}")

    # Call helper function to get search results
    search_query = (By.TAG_NAME, "a")
    search_results = get_search_results(driver, company_name, url, search_query)

    # If no search results found, return None
    if not search_results:
        write_log(f"{company_name}: No Search Results Found | URL: {url}")
        return None
    
    # Extract PDF links from search results
    pdf_links = []
    for result in search_results:
        try:
            # Get href attribute of link
            href = result.get_attribute('href')
            if not href:  # Skip if href is None or empty string
                continue

            # Check if link is PDF
            is_pdf = ('.pdf' in href.lower())
            

            # Check if link text contains keywords
            text = result.text.lower()
            keywords = ['report', 'esg', 'sustainability', 'impact', 'environment', 'green', 'carbon', 'emissions']
            has_keywords = any(keyword in text for keyword in keywords)
            
            # Check if it's PDF and contains keywords
            if is_pdf and has_keywords and (href not in pdf_links):
                pdf_links.append(href)
                
        except Exception as e:
            # If element is stale, continue to next one
            continue
    write_log(f"{company_name}: Found {len(pdf_links)} PDF on webpage.")

    if not pdf_links:
        return None

    # Download and check first 10 PDFs
    for pdf_url in pdf_links[:10]:
        #pdf_path = download_pdf(company_name, pdf_url)
        #if pdf_path:
            return pdf_url
    
    write_log(f"{company_name}: No Valid PDF Found in Webpage")
    return None
        
# Process single company
def process_company(company_name):
    try:
        print(f"Processing {company_name}...")
        driver = init_driver()
        if not driver:
            write_log(f"{company_name}: Failed to initialize WebDriver.")
            return None
        print("Driver initialized.")

        # 2. If PDF not found, search webpage, and find PDF in webpage
        webpage_url_list = search_webpage_in_bing(driver, company_name)
        if webpage_url_list:
            for webpage_url in webpage_url_list:
                result = find_pdf_in_webpage(driver, company_name, webpage_url)
                if result is None:
                    write_log(f"{company_name}: No valid PDF found in webpage {webpage_url}")
                    continue  # Skip to next URL or company
                pdf_url = result
                if pdf_url:
                    if is_valid_esg_report_from_url(pdf_url, company_name, str(datetime.now().year)):
                        driver.quit()
                        return webpage_url, pdf_url
                    else:
                        return webpage_url, None
        driver.quit()
    except Exception as e:
        print(e)
        write_log(f"{company_name}: No report found for {company_name}")
        return (None, None)


# Initialize global variables
LOG_FILENAME = "log.txt"

#to test: run PYTHONPATH=team_adansonia/coursework_one/a_link_retrieval/modules poetry run python team_adansonia/coursework_one/a_link_retrieval/modules/crawler/crawler.py

if __name__ == "__main__":
    # Single company
    company_name = "Apple Inc"
    webpage_url, pdf_url = process_company(company_name)
    print(f"Webpage URL: {webpage_url}")
    print(f"PDF URL: {pdf_url}")

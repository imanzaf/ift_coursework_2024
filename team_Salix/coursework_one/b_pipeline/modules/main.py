"""
CSR Report PDF Downloader

This module provides functionality for asynchronously downloading CSR (Corporate Social Responsibility) 
report PDFs from URLs specified in a CSV file. It includes features for progress tracking, error logging,
and detailed download statistics.

The module uses asyncio and aiohttp for efficient concurrent downloads, with built-in rate limiting
to prevent overwhelming servers. It also includes comprehensive error handling and detailed logging
of both successful and failed downloads.

Example:
    To run the downloader::

        $ python main.py

The CSV file should contain at least the following columns:
    - company: Name of the company
    - year: Year of the CSR report
    - url: Download URL for the PDF

Note:
    This script is compatible with Jupyter Notebook environments through the use of nest_asyncio.
"""

import os
import aiohttp
import asyncio
import pandas as pd
import random
import time
from tqdm.asyncio import tqdm
import nest_asyncio  # Compatible with Jupyter Notebook

nest_asyncio.apply()  # Apply for Jupyter Notebook

# Configuration Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))  # Get project root directory

# Set cleaned_url.csv path (a_pipeline/aresult/cleaned_url.csv)
CSV_PATH = os.getenv(
    "CSV_PATH", 
    os.path.join(PROJECT_ROOT, "coursework_one", "a_pipeline", "aresult", "cleaned_url.csv")
)

# Print path for debugging
print(f"Looking for CSV at: {CSV_PATH}")

# Set PDF download root directory to b_pipeline/bresult/csr-reports
DOWNLOAD_ROOT = os.getenv(
    "DOWNLOAD_PATH",
    os.path.join(os.path.dirname(BASE_DIR), "bresult", "csr_reports")
)
print(f"PDF files will be saved to: {DOWNLOAD_ROOT}")
os.makedirs(DOWNLOAD_ROOT, exist_ok=True)  # Ensure directory exists

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"❌ Cannot find `{CSV_PATH}`, please check if the file exists!")

df = pd.read_csv(CSV_PATH)

# Ensure required columns exist
required_columns = {"company", "year", "url"}
if not required_columns.issubset(df.columns):
    raise ValueError(f"CSV file missing required columns: {required_columns - set(df.columns)}")

# Limit concurrent downloads (adjustable)
MAX_CONCURRENT_DOWNLOADS = 1  # Download one at a time
semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

# Track download times
download_times = []

# Failed downloads log file (TXT format)
LOG_FILE = "download_failed.txt"

# Add User-Agent & fake Referer
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",  # Edge browser UA
    "Referer": "https://www.bing.com/search",
    "Accept": "application/pdf,application/octet-stream",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

def log_failed_download(url: str, reason: str) -> None:
    """
    Log failed download attempts to a text file.

    Args:
        url (str): The URL that failed to download
        reason (str): The reason for the download failure

    Note:
        The log entries are appended to the file specified by LOG_FILE
    """
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"Failed: {url} | Reason: {reason}\n")

def log_statistics(stats_info: str) -> None:
    """
    Write download statistics to the log file.

    Args:
        stats_info (str): Formatted string containing statistics information

    Note:
        The statistics are appended to the file specified by LOG_FILE,
        separated by delimiter lines for better readability
    """
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write("\n" + "="*50 + "\n")
        log_file.write("Download Statistics\n")
        log_file.write("="*50 + "\n")
        log_file.write(stats_info)
        log_file.write("\n" + "="*50 + "\n")

async def download_pdf(session: aiohttp.ClientSession, row: pd.Series, overall_progress: tqdm) -> bool:
    """
    Download a single PDF file asynchronously.

    Args:
        session (aiohttp.ClientSession): Active aiohttp session for making requests
        row (pd.Series): Pandas Series containing company, year, and url information
        overall_progress (tqdm): Progress bar object for tracking overall download progress

    Returns:
        bool: True if download was successful, False otherwise

    Note:
        This function includes progress tracking for individual files and
        automatically creates necessary directories for saving the PDF.
        It also handles various error cases and logs failures appropriately.
    """
    company = row['company']
    year = str(row['year'])
    url = row['url']
    
    save_dir = os.path.join(DOWNLOAD_ROOT, company, year)
    save_path = os.path.join(save_dir, f"{company}_{year}.pdf")

    print(f"\nAttempting to download: {company} {year}")
    print(f"URL: {url}")

    async with semaphore:
        start_time = time.time()

        try:
            async with session.get(url, headers=HEADERS) as response:
                if response.status == 200:
                    total_size = int(response.headers.get("content-length", 0))
                    chunk_size = 1024
                    downloaded = 0

                    # Create progress bar for single file
                    with tqdm(total=total_size, unit='B', unit_scale=True, 
                            desc=f"Downloading {company}_{year}", leave=True) as file_progress:
                        
                        # Only create directory on HTTP 200
                        os.makedirs(save_dir, exist_ok=True)

                        with open(save_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                f.write(chunk)
                                downloaded += len(chunk)
                                file_progress.update(len(chunk))

                    download_time = time.time() - start_time
                    download_times.append({
                        'company': company,
                        'year': year,
                        'time': download_time,
                        'size': total_size
                    })
                    
                    speed = total_size / download_time / 1024 / 1024  # MB/s
                    print(f"✅ Successfully downloaded: {save_path}")
                    print(f"   Time: {download_time:.1f}s, Speed: {speed:.2f}MB/s")
                    
                    overall_progress.update(1)
                    return True
                else:
                    error_msg = f"HTTP {response.status}"
                    print(f"❌ Download failed: {error_msg}")
                    log_failed_download(url, error_msg)
                    return False

        except Exception as e:
            print(f"⚠️ Download error: {str(e)}")
            log_failed_download(url, str(e))
            return False

async def main() -> None:
    """
    Main execution function for the PDF downloader.

    This function:
        1. Sets up the download session
        2. Processes all URLs from the CSV file
        3. Tracks overall progress
        4. Collects and logs detailed statistics
        5. Handles errors and maintains download counts

    The function provides detailed progress information and statistics both
    during execution and after completion. It includes:
        - Overall download progress
        - Success and failure counts
        - Download speeds and times
        - Year-wise statistics
        - Records of fastest and slowest downloads

    Note:
        The function implements rate limiting through asyncio.sleep()
        to prevent overwhelming target servers.
    """
    start_time = time.time()
    success_count = 0
    failed_count = 0
    
    async with aiohttp.ClientSession() as session:
        total_files = len(df)  # Use complete df
        
        # Create overall progress bar
        with tqdm(total=total_files, desc="Overall Progress", unit="file") as overall_progress:
            for _, row in df.iterrows():  # Use complete df
                try:
                    result = await download_pdf(session, row, overall_progress)
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                    # Add delay to avoid too frequent requests
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Processing error: {str(e)}")
                    failed_count += 1
                    continue
        
        # Print statistics
        total_time = time.time() - start_time
        print("\n📊 Download Statistics:")
        print(f"Total files: {total_files}")
        print(f"Successfully downloaded: {success_count}")
        print(f"Failed downloads: {failed_count}")
        print(f"Total time: {total_time:.1f} seconds")
        
        if download_times:
            # Calculate average download time for each year
            year_stats = {}
            for item in download_times:
                year = item['year']
                if year not in year_stats:
                    year_stats[year] = {'times': [], 'sizes': []}
                year_stats[year]['times'].append(item['time'])
                year_stats[year]['sizes'].append(item['size'])
            
            # Collect statistics
            stats = []
            stats.append("\n📊 Download Statistics:")
            stats.append(f"Total files: {total_files}")
            stats.append(f"Successfully downloaded: {success_count}")
            stats.append(f"Failed downloads: {failed_count}")
            stats.append(f"Total time: {total_time:.1f} seconds")
            
            if download_times:
                # Statistics by year
                stats.append("\n📈 Download Statistics by Year:")
                for year in sorted(year_stats.keys()):
                    times = year_stats[year]['times']
                    sizes = year_stats[year]['sizes']
                    avg_time = sum(times) / len(times)
                    total_size = sum(sizes) / (1024 * 1024)
                    stats.append(f"\nYear {year}:")
                    stats.append(f"  - Successfully downloaded: {len(times)} files")
                    stats.append(f"  - Average download time: {avg_time:.1f} seconds")
                    stats.append(f"  - Total download size: {total_size:.1f}MB")
                    stats.append(f"  - Average download speed: {total_size/sum(times):.2f}MB/s")
                
                # Overall statistics
                stats.append("\n📊 Overall Statistics:")
                avg_time = sum(item['time'] for item in download_times) / len(download_times)
                total_size = sum(item['size'] for item in download_times) / (1024 * 1024)
                stats.append(f"Average download time: {avg_time:.1f} seconds")
                stats.append(f"Total download size: {total_size:.1f}MB")
                stats.append(f"Average download speed: {total_size/total_time:.2f}MB/s")
                
                # Fastest and slowest records
                fastest = min(download_times, key=lambda x: x['time'])
                slowest = max(download_times, key=lambda x: x['time'])
                stats.append(f"\n⚡️ Fastest download: {fastest['company']} ({fastest['year']}) - {fastest['time']:.1f} seconds")
                stats.append(f"🐌 Slowest download: {slowest['company']} ({slowest['year']}) - {slowest['time']:.1f} seconds")

            # Write statistics to log file
            stats_text = "\n".join(stats)
            print(stats_text)  # Print to console
            log_statistics(stats_text)  # Write to log file
        
        # Check failed downloads log
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
            print("\n⚠️ Failed download records:")
            with open(LOG_FILE, 'r') as f:
                print(f.read())

if __name__ == "__main__":
    asyncio.run(main())

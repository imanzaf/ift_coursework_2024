CSR Report Scraper Documentation
================================

This module automates the process of scraping CSR reports, downloading them as PDFs, and storing them in MinIO and MongoDB. The process is designed to:
1. Fetch a list of companies from a PostgreSQL database.
2. Use Selenium to search for CSR reports based on the company name and year.
3. Download CSR reports (PDFs) and store them locally.
4. Upload the downloaded reports to MinIO for storage.
5. Save the metadata (company name, report URL, storage path) to MongoDB.

---

## 1. Configuration

### Database Configuration (PostgreSQL)

The PostgreSQL configuration is provided in the `DB_CONFIG` dictionary. The database is used to store company details.

- **dbname**: `fift`
- **user**: `postgres`
- **password**: `postgres`
- **host**: `localhost`
- **port**: `5439`

---

### MongoDB Configuration

MongoDB is used for storing the metadata (company details, report URL, year, etc.) of CSR reports.

- **Mongo URI**: `mongodb://localhost:27019`
- **Database**: `csr_db`
- **Collection**: `csr_reports`

---

### MinIO Configuration

MinIO is used for uploading the actual CSR report files (PDFs).

- **Server**: `localhost:9000`
- **Access Key**: `ift_bigdata`
- **Secret Key**: `minio_password`
- **Bucket Name**: `csr-reports`

---

### Proxy Configuration

If a proxy is needed, it can be configured in the `PROXY` variable.

Example:
- **PROXY**: `"http://127.0.0.1:7890"`

---

## 2. Logging

Logs are written to both the terminal and a log file (`csr_fast.log`). The `write_log()` function records messages with timestamps.

**Log File**: `csr_fast.log`

The log messages are written with the format:


---

## 3. Core Functions

### `init_driver()`
Initializes and returns a Selenium Chrome WebDriver instance.

- **Purpose**: Launches a Chrome WebDriver instance to perform web scraping tasks.
- **Returns**: A Selenium WebDriver instance.

---

### `get_search_results()`
Searches for CSR reports on Bing and returns the search results.

- **Purpose**: Searches for CSR reports based on a query.
- **Parameters**:
  - `driver`: The Selenium WebDriver instance.
  - `query`: The search query string.
  - `timeout`: The maximum time to wait for the page to load (default is 5 seconds).
- **Returns**: A list of search result elements.

---

### `download_pdf()`
Downloads CSR report PDFs to local storage, with filenames based on the company name and report year.

- **Purpose**: Downloads the CSR report in PDF format.
- **Parameters**:
  - `company_name`: The name of the company.
  - `year`: The year of the CSR report.
  - `url`: The URL of the CSR report.
- **Returns**: The local file path if the download is successful, or `None` if failed.

---

### `upload_to_minio()`
Uploads the downloaded CSR report PDF to MinIO.

- **Purpose**: Uploads the downloaded PDF file to MinIO.
- **Parameters**:
  - `company_name`: The name of the company.
  - `year`: The year of the CSR report.
  - `local_path`: The local path to the downloaded PDF.
- **Returns**: The MinIO object name if upload is successful, or `None` if failed.

---

### `save_csr_report_info_to_mongo()`
Saves the CSR report metadata (company name, report URL, storage path) to MongoDB.

- **Purpose**: Stores the metadata related to the CSR report in MongoDB.
- **Parameters**:
  - `company_name`: The name of the company.
  - `pdf_url`: The URL to the CSR report.
  - `object_name`: The name of the uploaded report in MinIO.
  - `year`: The year of the CSR report.
- **Returns**: None (metadata is inserted into MongoDB).

---

### `get_company_list_from_postgres()`
Fetches a list of companies from the PostgreSQL database.

- **Purpose**: Retrieves the list of companies that will be used for searching CSR reports.
- **Returns**: A list of company names.

---

### `search_by_years()`
Searches for CSR reports by year and keywords, downloading and saving PDFs.

- **Purpose**: Searches for CSR reports by year and keywords, downloading matching reports.
- **Parameters**:
  - `driver`: The Selenium WebDriver instance.
  - `company_name`: The name of the company to search for.
  - `years`: The list of years to search.
  - `keywords`: The list of keywords for the search query.
- **Returns**: `True` if any reports are found and processed, otherwise `False`.

---

### `process_batch()`
Processes a batch of companies concurrently using multiple threads.

- **Purpose**: Processes the list of companies in parallel to speed up the report scraping process.
- **Parameters**:
  - `company_list`: The list of companies to process.
- **Returns**: None.

---

## 4. Main Execution

The main function retrieves the list of companies from PostgreSQL and starts the batch processing.

### Main Execution Steps:
1. Retrieve company list from PostgreSQL.
2. Check if the MinIO bucket exists; create it if necessary.
3. Start the batch processing of companies.

---

## Dependencies
------------------------

This script requires the following Python libraries:

- `requests`: For making HTTP requests.
- `psycopg2`: For interacting with PostgreSQL.
- `pymongo`: For interacting with MongoDB.
- `minio`: For interacting with MinIO.
- `selenium`: For web scraping with Chrome WebDriver.
- `chromedriver_autoinstaller`: For automatically installing ChromeDriver.

Install the dependencies using `pip`:

```bash
pip install requests psycopg2 pymongo minio selenium chromedriver_autoinstaller
```
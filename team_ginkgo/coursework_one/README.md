# Main Project Overview

This project is designed to build an automated data pipeline for fetching, storing, and managing Corporate Social Responsibility (CSR) reports. The system uses Google API to search for report links, downloads PDF files, uploads them to MinIO storage, and updates the relevant information in a PostgreSQL database. It supports multithreading and scheduled task execution.

## Main Project Features

### 1. Database Module (database.py)
- Initializes the database and creates the Ginkgo.csr_reports table.
- Inserts basic company information (e.g., company symbol, name, and report years).

### 2. Scraper Module (scraper.py)
- Uses Google Custom Search API to search for CSR reports (PDF files).
- Stores the scraped report URLs in the database.
- Supports multithreaded processing for improved efficiency.

### 3. MinIO Client Module (minio_client.py)
- Downloads CSR report PDFs and uploads them to MinIO object storage.
- Updates the minio_path field in the database with the MinIO file path.
- Supports multithreaded processing for faster file handling.

### 4. Scheduler Module (scheduler.py)
- Implements task scheduling using apscheduler.
- Automatically runs data scraping and file upload tasks quarterly (January, April, July, October).

### 5. Main Entry Point (main.py)
- Provides an interactive interface for users to:
  1. Manually run all scripts.
  2. Start scheduled tasks.
  3. Exit the program.

## Directory Structure
```
team_Ginkgo/
│
├── modules/               # Main project modules
│   ├── config.py          # Configuration file containing API and database settings
│   ├── database.py        # Database initialization and data insertion module
│   ├── main.py            # Main entry point for manual execution and scheduling
│   ├── minio_client.py    # Module for interacting with MinIO object storage
│   ├── scheduler.py       # Task scheduling module
│   └── scraper.py         # Data scraping module using Google API to search PDF reports
```

## Running Project

### Prerequisites
Before running the project, ensure you have the following:

- Python Version: *Python 3.8* or above is recommended.
- Required Libraries:
  - psycopg2: For PostgreSQL database operations
  - google-api-python-client: For Google Custom Search API
  - minio: For interacting with MinIO object storage
  - selenium and webdriver-manager: For handling PDF downloads
  - apscheduler: For task scheduling
  - requests: For HTTP requests
  - concurrent.futures: For multithreading

Install dependencies:
```bash
pip install -r requirements.txt  # Install dependencies
```

### Configuration
The *modules/config.py* file contains configuration details for Google API, database, and MinIO. Below is an example configuration:

```python
# Google API Configuration
GOOGLE_API_KEY = "your_google_api_key"
GOOGLE_CX = "your_google_custom_search_engine_id"

# Database Configuration
DB_CONFIG = {
    "dbname": "your_database_name",
    "user": "your_database_user",
    "password": "your_database_password",
    "host": "your_database_host",
    "port": 5432
}

# MinIO Configuration
MINIO_CONFIG = {
    "endpoint": "localhost:9000",
    "access_key": "your_minio_access_key",
    "secret_key": "your_minio_secret_key",
    "bucket": "your_bucket_name"
}
```
Update these configurations as per your requirements.

### Usage Instructions

1. Configure the Project:
Update the config.py file with your Google API, database, and MinIO settings.

2. Initialize the Database:
Run *database.py* to create the necessary tables and insert initial data.
  ```bash
  pyt*hon ./modules/database.py
  ```

3. Scrape CSR Report URLs:
Run *scraper.py* to use the Google API to search for CSR report URLs.
  ```bash
  python ./modules/scraper.py
  ```

4. Download and Upload Reports:
Run *minio_client.py* to download PDF files and upload them to MinIO while updating the database.
  ```bash
  python ./modules/minio_client.py
  ```

5. Start Task Scheduling:
Run *scheduler.py* to enable quarterly automatic execution of tasks.
  ```bash
  python ./modules/scheduler.py
  ```

6. Use Interactive Interface:
Run *main.py* to manually execute scripts or start scheduling tasks.
  ```bash
  python ./modules/main.py
  ```

> - Ensure that the PostgreSQL database and MinIO services are properly configured and running.
> - The Google API has usage quotas. Use it wisely to avoid exceeding limits.
> - Adjust Selenium configurations and wait times as needed for PDF downloads.
> - For multithreaded processing, you can configure the number of threads based on your system's performance.

## Code Quality Checks
The project enforces code quality standards using `flake8`, `black`, `isort`, and `bandit`:
```bash
poetry run flake8 ./modules  # Linting
poetry run black --check ./modules  # Formatting check
poetry run isort --check-only ./modules  # Import sorting check
poetry run bandit -r ./modules  # Security scan
```

## Conclusion
This project automates the process of fetching, storing, and managing CSR reports. It supports multithreaded execution and scheduled task management, making it efficient for handling large-scale data. Always ensure to run the scripts in the correct order and verify the configurations before deployment.

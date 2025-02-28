Architecture Overview
=====================

System Components
-----------------
The CSR Report Data Processing System consists of:

1. **Database Module (`database.py`)**  

   - Creates `Ginkgo.csr_reports` table in PostgreSQL.
   - Stores company symbols, names, report years, and URLs.

2. **Data Scraper (`scraper.py`)**  

   - Uses Google Custom Search API to find CSR PDF reports.
   - Saves report URLs to PostgreSQL.

3. **MinIO Storage (`minio_client.py`)**  

   - Downloads PDFs and uploads them to MinIO.
   - Updates PostgreSQL with MinIO storage paths.

4. **Scheduler (`scheduler.py`)**  

   - Runs `database.py`, `scraper.py`, and `minio_client.py` **every quarter**.

5. **Main Controller (`main.py`)**  

   - Provides a CLI for users to manually run scripts or schedule tasks.

Technology Stack
----------------
- **Python** (Backend Processing)
- **PostgreSQL** (Structured Data Storage)
- **MinIO** (Object Storage for PDFs)
- **Google Custom Search API** (CSR Report Discovery)
- **Docker** (Containerization)
- **APScheduler** (Task Scheduling)

System Workflow
---------------
1. **Database Initialization** (`database.py`)  

   - Creates tables and populates them with companies.

2. **Scraping Reports** (`scraper.py`)  

   - Searches for CSR PDFs using Google API.
   - Updates PostgreSQL with report URLs.

3. **Downloading & Storing Reports** (`minio_client.py`)  

   - Downloads PDFs from URLs.
   - Uploads PDFs to MinIO.
   - Updates PostgreSQL with MinIO paths.

4. **Scheduling Execution** (`scheduler.py`)  

   - Automatically triggers the above steps **every quarter**.


# **CSR Data Pipeline & Data Lake**

**Author**: *Magnolia*  
**Version**: 1.0.0  
**License**: MIT (or your choice)

This repository automates the **scraping**, **cleaning**, **storage**, **retrieval**, and **analysis** of Corporate Social Responsibility (CSR) reports. We use **Selenium**, **MongoDB**, **MinIO**, **PostgreSQL**, and **FastAPI** to ensure a robust, maintainable, and highly scalable system.

---

## **Table of Contents**
1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
   - [Main Subcommands](#main-subcommands)
   - [Scripts](#scripts)
6. [Data Lake Design](#data-lake-design)
7. [Docker & docker-compose](#docker--docker-compose)
8. [Code Quality & Testing](#code-quality--testing)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)
11. [License](#license)

---

## **1. Overview**

In a world increasingly focused on **ESG metrics**, the timeliness and accuracy of **CSR reports** matter greatly to stakeholders, researchers, and data scientists. **CSR Data Pipeline** aims to:

- **Scrape** thousands of CSR PDF reports from corporate websites or search engines.  
- **Clean & Validate** metadata (e.g., correcting out-of-range years, removing duplicates).  
- **Store** final PDF files in **MinIO** (S3-compatible) and metadata in **MongoDB** or **PostgreSQL**.  
- **Provide** a **FastAPI** endpoint to easily search and download these reports.  
- **Offer** an optional analysis layer (e.g. text extraction, sentiment checks).  
- Maintain high **code quality** using best practices (Black, Flake8, Pytest).

---

## **2. Directory Structure**

Below is the recommended layout (based on your final structure):

```
coursework_one/
├── config/
│   └── conf.yaml                # YAML configuration (e.g. credentials, environment)
│
├── modules/
│   ├── __init__.py              # Makes 'modules' a Python package
│   ├── api/
│   │   ├── analysis_pipeline.py # Analysis logic (text extraction, sentiment)
│   │   ├── fastapi_api.py       # FastAPI server
│   │   ├── mongo_index_setup.py # Script to create MongoDB indexes
│   │   └── streamlit_app.py     # (Optional) A Streamlit UI
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── db_connection.py     # PostgreSQL or MongoDB connection utilities
│   │
│   ├── minio_ops/
│   │   ├── minio_client.py      # MinIO client logic
│   │
│   └── scraper/
│       ├── reports/             # Downloaded PDF reports
│       ├── temp_reports/        # Temporary or staging files
│       ├── csr_extractor.log    # Logs from extraction
│       ├── csr_fast.log         # Additional logs
│       ├── csr_fix_and_cleanup.log
│       ├── csr_fix_and_cleanup.py # Fix script (year correction, duplicates removal)
│       └── csr_scraper.py       # Core scraping logic
│
├── pyproject.toml               # Python packaging config, dependencies
├── poetry.lock                  # If using Poetry
├── scripts/
│   ├── run_api.sh               # Shell script to run the API
│   └── run_scraper.sh           # Shell script to run the scraper
│
├── static/
│   # (Potentially for images/CSS/JS if Streamlit or other frontends)
│
├── test/
│   ├── conftest.py
│   ├── test_csr_scraper.py      # Pytest for the scraper
│   └── test_fastapi_api.py      # Pytest for FastAPI
│
├── docker-compose.yml           # Orchestrates DBs, MinIO, Kafka, etc.
├── main.py                      # Project entry script with argparse subcommands
├── README.md                    # This documentation
└── scraper_cron.log            # Logs from cron-based scraping (optional)
```

**Key Modules**:  
- `csr_scraper.py` (scraping pipeline)  
- `csr_fix_and_cleanup.py` (cleaning tasks)  
- `analysis_pipeline.py` (analysis tasks)  
- `fastapi_api.py` (FastAPI server)  
- `mongo_index_setup.py` (MongoDB indexes)

---

## **3. Installation**

1. **Clone** this repository:
   ```bash
   git clone https://github.com/yourusername/csr_data_project.git
   cd coursework_one
   ```
2. **Install dependencies** using your `pyproject.toml`:
   ```bash
   pip install .
   ```
   Or with `requirements.txt` if you prefer:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) **Activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install .
   ```
4. **Check**:
   ```bash
   python main.py --help
   ```

---

## **4. Configuration**

- **conf.yaml** (in `config/`) can store environment settings such as:
  ```yaml
  MONGO_URI: "mongodb://localhost:27019"
  MINIO_HOST: "localhost"
  MINIO_BUCKET: "csr-reports"
  POSTGRES_HOST: "localhost"
  POSTGRES_PORT: 5439
  POSTGRES_DBNAME: "postgres"
  POSTGRES_USER: "postgres"
  POSTGRES_PASSWORD: "postgres"
  ```
- **Environment Variables**: Alternatively, set them via `.env` or your OS environment.  
- **docker-compose.yml**: Orchestrates containers for `mongo_db_cw`, `postgres_db_cw`, `miniocw` (MinIO), `pgadmin`, `zookeeper`, `kafka`, etc.

---

## **5. Usage**

### **Main Subcommands**

`main.py` includes **argparse** subcommands. Common usage:

```bash
python main.py [command] [options]
```

1. **Scrape**  
   ```bash
   python main.py scrape --max-companies 20
   ```
   Runs the core pipeline in `csr_scraper.py`. The `--max-companies` argument can limit the number of companies to scrape for testing.

2. **Analysis**  
   ```bash
   python main.py analysis --quick
   ```
   Executes `analysis_pipeline.py` tasks, e.g., text extraction, sentiment, or keyword extraction. `--quick` might skip heavier computations.

3. **Fix**  
   ```bash
   python main.py fix --dry-run
   ```
   Calls `csr_fix_and_cleanup.py` to correct years (e.g., bounding 2015–2024) and remove duplicates. `--dry-run` means it logs changes without applying them.

4. **Index**  
   ```bash
   python main.py index
   ```
   Invokes `mongo_index_setup.py` to create or update your MongoDB indexes (e.g. text or compound indexes).

5. **API**  
   ```bash
   python main.py api --host 0.0.0.0 --port 8000 --reload
   ```
   Launches the **FastAPI** server from `fastapi_api.py`. Access it at `http://localhost:8000/docs`.

### **Scripts**

- **`run_api.sh`**: Automates checking if Mongo/MinIO are up, then starts the API in the background.  
- **`run_scraper.sh`**: Potentially calls `python main.py scrape` with any arguments you want, plus logging.

---

## **6. Data Lake Design**

We implement an **S3-like data lake** in MinIO:

- **Raw Zone**:
  ```
  minio
  └── csr-reports/
      ├── 2023/
      │   ├── Apple_Inc.pdf
      │   └── ...
      ├── 2024/
      │   ├── ...
      ...
  ```
- **Metadata in MongoDB** or **PostgreSQL**:
  - `company_name`
  - `csr_report_year`
  - `storage_path`
  - `ingestion_time`
  - (etc.)

When you query **FastAPI**:
1. The code looks up metadata in MongoDB/Postgres.  
2. Fetches the real PDF path from MinIO if needed.  
3. Returns results to the user or a bulk ZIP download.

**Future expansions** could involve a “Processed Zone” storing text-extracted data, or an “Analytics Zone” with aggregated ESG metrics.

---

## **7. Docker & docker-compose**

In your `docker-compose.yml`, containers might include:
- `mongo_db_cw` (MongoDB)
- `postgres_db_cw` (PostgreSQL)
- `pg_admin_cw` (pgAdmin for DB management)
- `miniocw` + `minio_client_cw` (MinIO + client to auto-create buckets)
- `zookeeper_cw` / `kafka_cw` (if you use Kafka)
  
**Example**:
```bash
docker-compose up -d
```
Then connect locally:
- MongoDB: `mongodb://localhost:27019`
- PostgreSQL: `psql -h localhost -p 5439 -U postgres`
- MinIO: `http://localhost:9001`, user `ift_bigdata`, pass `minio_password`
- pgAdmin: `http://localhost:5051`

Check the logs:
```bash
docker-compose logs -f
```

---

## **8. Code Quality & Testing**

1. **Formatting (Black)**  
   ```bash
   black .
   ```
2. **Linting (Flake8)**  
   ```bash
   flake8 .
   ```
3. **Testing (Pytest)**  
   ```bash
   pytest test/
   ```
   - `test_csr_scraper.py` checks scraping logic (Selenium calls, PDF downloads).  
   - `test_fastapi_api.py` verifies the API endpoints.

**Continuous Integration**: If using GitHub Actions, you can run all three steps on every pull request to keep the repo stable.

---

## **9. Troubleshooting**

1. **Scraper Times Out**  
   - Check if the remote site is blocking you. Possibly reduce concurrency or enable proxy usage in `csr_scraper.py`.

2. **MongoDB or MinIO Connection Error**  
   - Confirm correct environment variables.  
   - For Docker, verify the ports in your `docker-compose.yml` (e.g., `27019:27017` or `9000:9000`).

3. **API Returns 500**  
   - Inspect the logs in `csr_fast.log` or standard output. Possibly a missing PDF in MinIO or the year is out of the corrected range.

4. **Data Not Found in pgAdmin**  
   - In pgAdmin, add a server with `hostname=postgres_db`, `port=5432`, `username=postgres`, `password=postgres`.  
   - Make sure the container name references match.

---

## **10. Contributing**

We welcome **bug reports**, **feature requests**, and **pull requests**!  
- Fork the repo & create a feature branch.  
- Ensure you pass `black .`, `flake8 .`, and `pytest test/`.  
- Open a Pull Request describing your changes.

If you have questions, open an **issue** in this repository—happy to help!

---

## **11. License**

This project is distributed under the **MIT License** (or your chosen license). See the `LICENSE` file or `pyproject.toml` for more details.

---

**Thank you** for using the CSR Data Pipeline! If you run into any problems, feel free to create an issue or reach out. We hope this pipeline significantly eases the complexity of collecting, validating, and distributing CSR reports for your analyses. **Happy coding and data-lake building!**
# CSR Report Crawler and Storage System

⚠️ **IMPORTANT NOTICE**
- The `docker-compose.yml` file in the root directory contains incorrect Iceberg network configurations and should not be used.
- We have provided a corrected version of the Docker Compose file inside the `team_Salix` directory.
- Please follow the installation instructions exactly as written - do NOT move any configuration files out of the `team_Salix` directory.
- All commands should be executed from within the `team_Salix` directory as specified in the installation guide below.

**Make sure to use our updated versions of these files for proper system functionality.**

## Overview
This project implements an automated system for crawling, downloading, and storing Corporate Social Responsibility (CSR) reports from various companies. The system consists of two main pipelines and includes automated scheduling for periodic updates.

## Project Structure
```
team_Salix/coursework_one/
├── a_pipeline/                  # Pipeline A: URL Crawling System
│   ├── aresult/                # Storage for crawler results
│   │   ├── cleaned_url.csv     # Processed and validated URLs
│   │   └── crawler_logs/       # Crawler execution logs
│   └── modules/
│       ├── main.py            # Main URL crawler implementation
│       └── notfoundclean.py   # URL validation and cleaning
│
├── b_pipeline/                  # Pipeline B: PDF Processing System
│   ├── bresult/                # Storage for PDF processing results
│   │   ├── csr_reports/       # Downloaded CSR reports
│   │   ├── download_failed.txt # Failed download records
│   │   └── pdf_check_report.csv # PDF validation results
│   └── modules/
│       ├── main.py            # PDF downloader implementation
│       ├── check_pdf.py       # PDF validation and verification
│       └── remove_damaged.py   # Cleanup for corrupted files
│
├── docs/                       # Documentation
│   ├── build/                 # Generated documentation files
│   │   └── html/             # HTML format documentation
│   └── source/               # Documentation source files
│       ├── api/              # API documentation
│       ├── modules/          # Module documentation
│       └── conf.py           # Sphinx configuration
│
├── tests/                      # Test Suite
│   ├── a_pipeline/           # Tests for Pipeline A
│   ├── b_pipeline/           # Tests for Pipeline B
│   └── conftest.py           # Test configurations
│
├── scheduler.py                # Automated task scheduler
├── upload_to_minio.py          # MinIO storage integration
├── pyproject.toml              # Project dependencies and config
├── poetry.lock                 # Locked dependencies
└── README.md                   # Project documentation
```

## Features

### Pipeline A: URL Crawler
- Extracts company names from SQLite database
- Searches for CSR reports using multiple search strategies
- Supports various report types (sustainability, ESG, CSR, etc.)
- Implements intelligent URL validation and filtering
- Outputs cleaned URLs to CSV format

### Pipeline B: PDF Handler
- Asynchronous PDF downloading with progress tracking
- PDF validation and integrity checking
- Automatic removal of damaged files
- Organized storage structure by company and year
- Detailed download statistics and logging

### Storage System
- MinIO object storage integration
- Structured storage hierarchy
- PostgreSQL database for metadata storage
- Support for multiple file versions

### Additional Features
- Automated weekly scheduling (Mondays at 3:00 AM)
- Comprehensive logging system
- Progress tracking and statistics
- Error handling and recovery
- Docker containerization support

## Dependencies
- Python 3.13+
- Key Python packages:
  - pandas >= 2.2.3
  - selenium >= 4.29.0
  - boto3 >= 1.36.26
  - aiohttp >= 3.11.13
  - PyPDF2 >= 3.0.1
  - psycopg2-binary >= 2.9.10
  - APScheduler >= 3.10.1

## Installation Guide and Usage Instructions
"If anyone wants to run our project locally, simply open the terminal and follow the steps below."

---
   ## *Step 1: Navigate to the Project Directory*
Before running any commands, open a terminal and navigate to the *team_Salix* directory:
⁠ bash
cd path/to/team_Salix
 ⁠

---

  ## *Step 2: Clean Up Old Docker Containers*
Before starting fresh, remove all *previous Docker containers, networks, and images*:
⁠ bash
docker stop $(docker ps -aq) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
docker network prune -f
docker volume prune -f
docker system prune -a -f
 ⁠

---

  ## *Step 3: Verify Docker & Poetry Installation*
Run the following commands to check if *Docker and Poetry* are installed:
⁠ bash
docker --version
poetry --version
 ⁠

---

  ## * Step 4: Start Docker Services*
Once Docker is verified, *start all required services*:
⁠ bash
docker compose up --build -d
 ⁠

---

  ## Step 5: Install Python Dependencies*
Once Docker is running, install all required *Python dependencies*:
⁠ bash
cd coursework_one
rm -rf .venv
poetry env remove --all
poetry install --no-root
 ⁠

---

  ## Step 6: Execute the Full Pipeline (Manual Execution)

⚠️ Important: DO NOT run all scripts at once!
The first script takes 5+ hours to fully complete. Instead, follow this staged approach:

1️⃣ Run Initial Data Extraction (Wait 10-15 minutes)
poetry run python a_pipeline/modules/main.py
Let this run for at least 15-20 minutes.
Then manually stop it by pressing CTRL + C.
Why?
Running for at least 15-20 minutes ensures that data processing starts and allows later scripts to execute correctly.
2️⃣ Continue with the Remaining Scripts (One by One)
Once a_pipeline/modules/main.py is manually stopped, run the remaining scripts in order:

poetry run python a_pipeline/modules/notfoundclean.py
poetry run python b_pipeline/modules/main.py
poetry run python b_pipeline/modules/check_pdf.py
poetry run python b_pipeline/modules/remove_damaged.py
⚠️ Run each script one at a time and let it fully complete before running the next!

3️⃣ Upload Processed Data to MinIO
Finally, run:

poetry run python upload_to_minio.py
This script uploads the extracted CSR reports to MinIO and syncs data with PostgreSQL.

---

  ## Step 7: Generate and View Project Documentation*
After running the pipeline, you can generate and view the detailed API documentation and guides:
```bash
# Generate documentation
cd docs
poetry run make html

# View in browser (choose based on your OS)
cd coursework_one/docs
open build/html/index.html  # On macOS
# or
xdg-open build/html/index.html  # On Linux
# or manually open in your browser
```
The documentation includes:
- Complete API reference
- Module descriptions
- Usage examples
- Search functionality

---

  ## Step 8: Enable Automatic Weekly Updates*
To automate the process *every week*, first ensure you're in the correct directory:
⁠ bash
cd ..  # Return to coursework_one directory if you're in docs
poetry run python scheduler.py
 ⁠

---

## Running Tests
To ensure the system is working correctly, run the test suite:

⚠️ **Test Dependencies**
Before running tests, you need to either:
1. Run Pipeline A first to generate the required `cleaned_url.csv` file, or
2. Use the provided mock data in `tests/mock_data/` directory

```bash
# Make sure you're in the team_Salix directory
cd path/to/team_Salix/coursework_one

# Option 1: Generate required test data first
poetry run python a_pipeline/modules/main.py
poetry run python a_pipeline/modules/notfoundclean.py

# Option 2: Use mock data (recommended for testing)
cp tests/mock_data/cleaned_url.csv a_pipeline/aresult/

# Then run the tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=. tests/

# Run specific test files
poetry run pytest tests/a_pipeline/  # Test Pipeline A
poetry run pytest tests/b_pipeline/  # Test Pipeline B

# Run tests with detailed output
poetry run pytest -v
```

The test suite includes:
- Unit tests for both pipelines
- Integration tests for the complete workflow
- Mock tests for external services
- Validation tests for PDF processing
- Error handling tests

Note: Some tests use mock data to avoid dependencies on external services and long-running processes. This ensures tests can run quickly and reliably in any environment.

## Configuration
The system uses environment variables for configuration:
- `MINIO_ENDPOINT`: MinIO server endpoint (default: http://localhost:9000)
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `POSTGRES_HOST`: PostgreSQL host
- `POSTGRES_PORT`: PostgreSQL port
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password

## Docker Support
The project includes Docker configuration for all required services:
- PostgreSQL database
- MinIO object storage
- MongoDB (for future extensions)
- pgAdmin for database management

## Logging
- Crawler logs: `a_pipeline/aresult/crawler_log_[timestamp].txt`
- Download logs: `b_pipeline/bresult/download_failed.txt`
- PDF validation report: `b_pipeline/bresult/pdf_check_report.csv`

## Error Handling
- Automatic retry for failed downloads
- Damaged PDF detection and removal
- Comprehensive error logging
- Transaction rollback support

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT License

Copyright (c) 2024 Team Salix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Documentation
The project uses Sphinx for documentation generation. The documentation includes detailed API references, module descriptions, and usage guides.

### Viewing Documentation
You can access the documentation in two ways:

1. **HTML Documentation**
   - Navigate to `docs/build/html/`
   - Open `index.html` in your web browser
   - Browse through:
     - Project overview
     - Module documentation
     - API reference
     - Search functionality

2. **Source Documentation**
   - Documentation source files are in `docs/source/`
   - Module documentation in `docs/source/modules/`
   - Configuration in `docs/source/conf.py`

### Generating Documentation
To generate or update the documentation:

1. Install dependencies (if not already done):
```bash
poetry install --no-root
```

2. Generate HTML documentation:
```bash
cd docs

```

3. View the documentation:
```bash
open build/html/index.html  # On macOS
# or
xdg-open build/html/index.html  # On Linux
# or manually open in your browser
```

### Documentation Structure
- **Project Overview**: General introduction and setup guide
- **Module Documentation**:
  - A Pipeline: URL crawling functionality
  - B Pipeline: PDF processing functionality
  - MinIO Upload: Storage management
  - Scheduler: Task automation
- **API Reference**: Detailed function and class documentation
- **Search**: Full-text search functionality


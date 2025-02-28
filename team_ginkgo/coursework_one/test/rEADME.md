# Test Directory Overview

This directory contains various tests to ensure the correctness, reliability, and security of the project components. The tests cover unit tests, integration tests, and end-to-end tests for the data extraction, processing, storage, and retrieval functionalities.

## Test Categories

### 1. Unit Tests
Unit tests verify the functionality of individual modules:
- **`test_unit/test_scraper.py`**: Tests the scraping functionality, ensuring CSR reports can be fetched from external sources.
- **`test_unit/test_database.py`**: Tests database schema, connection, and data insertion.
- **`test_unit/test_minio.py`**: Tests MinIO object storage, ensuring PDFs are uploaded and retrieved correctly.
- **`test_unit/test_scheduler.py`**: Tests task scheduling and script execution using APScheduler.
- **`test_unit/test_web.py`**: Tests FastAPI and Flask endpoints for retrieving CSR reports.

### 2. Integration Tests
Integration tests ensure that different components work together properly:
- **`test_pipeline/test_pipeline.py`**: Validates data flow from web scraping to storage in the database and MinIO.

### 3. End-to-End (E2E) Tests
End-to-end tests cover the entire data pipeline:
- **`test_end_to_end.py`**: Runs a full test from scraping a CSR report, downloading, storing in MinIO, and updating the database.

## Directory Structure
```
/test
    ├── test_unit/
    │   ├── test_scraper.py       # Tests web scraping and database updates
    │   ├── test_database.py      # Tests database schema, insertion, and constraints
    │   ├── test_minio.py         # Tests MinIO storage for CSR reports
    │   ├── test_scheduler.py     # Tests script scheduling
    │   ├── test_web.py           # Tests API endpoints (FastAPI & Flask)
    ├── test_pipeline/
    │   ├── test_pipeline.py      # Integration test for data pipeline
    ├── test_end_to_end.py        # End-to-end test covering full data pipeline
```

## Running Tests
To execute the tests, use `pytest`. Ensure dependencies are installed via `poetry`:
```bash
poetry install  # Install dependencies
poetry run pytest ./tests/  # Run all tests
```

### Running Specific Tests
- Run a single test file:
  ```bash
  poetry run pytest ./tests/test_unit/test_scraper.py
  ```
- Run with detailed output:
  ```bash
  poetry run pytest -v
  ```
- Run tests with coverage:
  ```bash
  poetry run pytest --cov=modules ./tests/
  ```

## Code Quality Checks
The project enforces code quality standards using `flake8`, `black`, `isort`, and `bandit`:
```bash
poetry run flake8 ./modules  # Linting
poetry run black --check ./modules  # Formatting check
poetry run isort --check-only ./modules  # Import sorting check
poetry run bandit -r ./modules  # Security scan
```

## Test Coverage Target
The project aims for at least **80% test coverage** to ensure robustness.

## Conclusion
This test suite ensures the data pipeline is functional, scalable, and secure. Always run tests before committing new code to maintain stability.


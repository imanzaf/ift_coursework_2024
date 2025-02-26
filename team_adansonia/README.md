# UCL IFT - Big Data in Quantitative Finance Coursework 2024-25

This is the main repository for the coursework of the module Big Data in Quantitative Finance 2024-25.

## Project Structure

# Team Adansonia Project
team_adansonia
└── team_adansonia
    ├── src
        ├── scheduler
            ├── __init__.py
            └── scheduler.py
        ├── link_retrieval
            ├── __init__.py
            ├── crawler.py
            ├── minio.py
            ├── mongodb.py
            └── validation.py
        └── main.py
    ├── tests
        ├── test_scheduler.py
        ├── test_crawler.py
        ├── test_minio.py
        ├── test_mongodb.py
        └── test_validation.py
    ├── .env.template
    ├── docker-compose.yml
    ├── pyproject.toml
    ├── README.md
    └── poetry.lock



This project consists of two main pipelines: Scheduler and Link Retrieval. Each pipeline has its own set of modules and functionalities.

## Pipelines

### 1. Scheduler
The Scheduler pipeline is responsible for scheduling and managing tasks. It ensures that tasks are executed at the right time and in the correct order.

### 2. Link Retrieval
The Link Retrieval pipeline is responsible for fetching and processing web links. It consists of the following modules:
- **Crawler**: Fetches web pages and extracts links.
- **Minio**: Handles storage of crawled data using Minio.
- **MongoDB**: Manages database operations with MongoDB.
- **Validation**: Ensures data integrity and correctness.

## Instructions

### Running the Code
To run the entire project, execute the following command:

1. Install dependencies using Poetry:
    ```sh
    poetry install
    ```

2. Copy the [.env.template] file to a [.env] and update the `ROOT_DIR` to your local project directory:
    ```sh
    cp .env.template .env
    ```

3. Build and run the project using Docker Compose:
    ```sh
    docker-compose up --build

4. Run Main
```bash

poetry run python -m main
```

### Running Tests
To run the tests for the entire project, use the following command:
```bash
poetry run pytest
```

### Running Bandit
To run Bandit for security analysis on the entire project, use the following command:
```bash
poetry run bandit -r .
```

### Using Poetry
Poetry is used for dependency management and packaging. To install dependencies, run:
```bash
poetry install
```
To add a new dependency, use:
```bash
poetry add <package_name>
```
To update dependencies, run:
```bash
poetry update
```



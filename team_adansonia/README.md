# UCL IFT - Big Data in Quantitative Finance Coursework 2024-25

This is the main repository for the coursework of the module Big Data in Quantitative Finance 2024-25.

## Project Structure

## Team Adansonia Project

```bash
team_adansonia
├── coursework_1
│   ├── scheduler
│   │   ├── __init__.py
│   │   └── scheduler.py
│   ├── link_retrieval
│   │   ├── modules
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py
│   │   │   ├── minio.py
│   │   │   ├── mongodb.py
│   │   │   └── validation.py
│   │   └── tests
│   │      ├── test_main.py
│   │      ├── test_crawler.py
│   │      └── test_google_crawler.py
│   └── main.py
├── .env.template
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── poetry.lock
```

This project consists of two main pipelines: **Scheduler** and **Link Retrieval**. Each pipeline has its own set of modules and functionalities.

## Pipelines

### 1. Scheduler
The Scheduler pipeline is responsible for scheduling and managing tasks. It ensures that tasks are executed at the right time and in the correct order.

### 2. Link Retrieval
The Link Retrieval pipeline is responsible for fetching and processing web links. It consists of the following modules:

- **Crawler**: Fetches web pages and extracts links.
- **Minio**: Handles storage of crawled data using Minio.
- **MongoDB**: Manages database operations with MongoDB.
- **Validation**: Ensures data integrity and correctness.

## system requirements

To run this project, you need to make sure you have
- Docker installed (Docker Desktop for Mac/Windows) Link: https://www.docker.com/products/docker-desktop/
- At least 6GB of RAM usable by docker container
- At least 128GB of free space on hard drive available to docker.
- Python 3.10 or higher
- Poetry 2.1.1. or higher

to install poetry run the command below:
```bash
pip install poetry
```

This can be checked and adjusted on docker desktop settings.

## Instructions

### Environment Initialisation

1.**copy files from  team_adansonia/coursework_one/a_link_retrieval/config to the root of the project**
- .env.template to .env
- docker-compose.yml: this will modify the docker-compose to:
   - add binded volume for mongo service
   - add Jenkins service at localhost:9999
- pyproject.toml
- .gitignore

Or you can run this command in your terminal or CMD:

for Mac/Linux:
```bash
cat << 'EOF' > copy_files.sh
#!/bin/bash

# Define the source and destination directories
SOURCE_DIR="team_adansonia/coursework_one/a_link_retrieval/config"
DEST_DIR="."

# Copy .env.template to .env
if [ -f "$SOURCE_DIR/.env.template" ]; then
    cp "$SOURCE_DIR/.env.template" "$DEST_DIR/.env"
    echo "✅ Copied .env.template to .env"
else
    echo "❌ .env.template not found in $SOURCE_DIR"
fi

# Copy docker-compose.yml
if [ -f "$SOURCE_DIR/docker-compose.yml" ]; then
    cp "$SOURCE_DIR/docker-compose.yml" "$DEST_DIR/docker-compose.yml"
    echo "✅ Copied docker-compose.yml"
else
    echo "❌ docker-compose.yml not found in $SOURCE_DIR"
fi

# Copy pyproject.toml
if [ -f "$SOURCE_DIR/pyproject.toml" ]; then
    cp "$SOURCE_DIR/pyproject.toml" "$DEST_DIR/pyproject.toml"
    echo "✅ Copied pyproject.toml"
else
    echo "❌ pyproject.toml not found in $SOURCE_DIR"
fi

# Copy .gitignore
if [ -f "$SOURCE_DIR/.gitignore" ]; then
    cp "$SOURCE_DIR/.gitignore" "$DEST_DIR/.gitignore"
    echo "✅ Copied .gitignore"
else
    echo "❌ .gitignore not found in $SOURCE_DIR"
fi

# Delete the script itself
rm -- "$0"
EOF

chmod +x copy_files.sh
bash copy_files.sh
```

for Windows:
```bash
for %i in (.env.template:.env docker-compose.yml:docker-compose.yml pyproject.toml:pyproject.toml .gitignore:.gitignore) do @(for /f "tokens=1,2 delims=:" %a in ("%i") do @if exist "team_adansonia\coursework_one\a_link_retrieval\config\%a" (copy "team_adansonia\coursework_one\a_link_retrieval\config\%a" "%b" >nul & echo Copied %a to %b) else (echo File %a not found))
```

2.**In /.env, update the `ROOT_DIR_LOCAL` to your local project directory.**

### Running the App on Docker

1.**Build and run the project using Docker Compose:**

   ```bash
   docker-compose up --build
   ```

When the containers are running, all the scripts will be scheduled automatically by Jenkins. So it will start extracting past and current ESG reports at regular intervals. **Customising the job schedule** can be done by accessing the Jenkins dashboard at `http://localhost:9999`.

### Running and testing scripts on local

1.**Make sure that you have build and run the docker containers and they running, you can do so by running the command below:**

   ```bash
   docker-compose up --build
   ```
**if the containers has been built once, you can just run the command below:**

   ```bash
   docker-compose up
   ```

2.**Use poetry to install the dependencies:**

   ```bash
   poetry install
   ```

3.1.**Run the main function to test the project:**

   ```bash
   poetry run python -m team_adansonia.coursework_one.a_link_retrieval.main
   ```

3.2.**Run specific fundtions inside main.py**

   ```bash
   poetry run python -c "from main import <function_name>; <function_name>(<parameters>)"
   ```
   **for example:**

   ```bash
   poetry run python -c "from main import populate_database_jenkins; populate_database_jenkins(2)"
   ```
this will populate the database with all available historical reports from 2 companies

### Running queries

Please run the command below and follow the terminal instructions:

```bash
poetry run python -m team_adansonia.coursework_one.a_link_retrieval.modules.mongo_db.queries
```

### Running Tests

To run the tests for the entire project, use:

```bash
poetry run pytest
```

### Running Bandit

To run Bandit for security analysis on the entire project, use:

```bash
poetry run bandit -r .
```

### Using Poetry

Poetry is used for dependency management and packaging.

- To install dependencies, run:

  ```bash
  poetry install
  ```

- To add a new dependency, use:

  ```bash
  poetry add <package_name>
  ```

- To update dependencies, run:

  ```bash
  poetry update
  ```
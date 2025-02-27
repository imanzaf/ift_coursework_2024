# UCL IFT - Big Data in Quantitative Finance Coursework 2024-25

## Team Adansonia Project

This repository contains the coursework for the module *Big Data in Quantitative Finance* (2024-25). The project consists of two main pipelines: **Scheduler** and **Link Retrieval**, each with its own modules and functionalities.

---

## 📁 Project Structure
```
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
│   │   ├── tests
│   │   │   ├── test_main.py
│   │   │   ├── test_crawler.py
│   │   │   └── test_google_crawler.py
│   └── main.py
├── .env.template
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── poetry.lock
```

---

## 🚀 Pipelines

### 1️⃣ Scheduler
The **Scheduler** pipeline manages and schedules tasks, ensuring they execute at the correct time and in the right order.

### 2️⃣ Link Retrieval
The **Link Retrieval** pipeline fetches and processes web links. It consists of the following modules:
- **Crawler**: Fetches web pages and extracts links.
- **Minio**: Handles storage of crawled data using Minio.
- **MongoDB**: Manages database operations with MongoDB.
- **Validation**: Ensures data integrity and correctness.

---

## 📌 Instructions

### 🔧 Running the Code
1. **Install dependencies using Poetry:**
   ```sh
   poetry install
   ```

2. **Copy the `.env.template` file to `.env` and update the `ROOT_DIR` to your local project directory:**
   ```sh
   cp .env.template .env
   ```

3. **Build and run the project using Docker Compose:**
   ```sh
   docker-compose up --build
   ```

4. **Run Main:**
   ```sh
   poetry run python team_adansonia/coursework_1/link_retrieval/main.py
   ```

### 📊 Running Queries
To run queries, use the following command and follow the terminal instructions:
```sh
poetry run python team_adansonia/coursework_1/link_retrieval/modules/mongodb/queries.py
```

### 🧪 Running Tests
To execute tests for the entire project:
```sh
poetry run pytest
```

### 🔍 Running Bandit (Security Analysis)
To run Bandit for security analysis:
```sh
poetry run bandit -r .
```

---

## 📦 Using Poetry

- **Install dependencies:**
  ```sh
  poetry install
  ```
- **Add a new dependency:**
  ```sh
  poetry add <package_name>
  ```
- **Update dependencies:**
  ```sh
  poetry update
  ```

---

### 📌 Notes
Ensure that all dependencies are installed correctly and environment variables are properly set up before running the project. If you encounter any issues, refer to the documentation or seek support from your team.




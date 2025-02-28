# Web Search Project

This project is a web application built with Flask and FastAPI. Users can query company annual reports via a frontend interface, and the results will be displayed on the page. The backend uses PostgreSQL for data storage and MinIO for file storage. The project supports querying data through a RESTful API.

## Main Project Features

### 1. API Module (api.py)
- Provides an API endpoint (/report) for querying CSR reports by company name or stock symbol and year.
- Connects to a PostgreSQL database to fetch report details such as:
  - Company Name
  - Stock Symbol
  - Report URL
  - MinIO Storage Path
- Supports fuzzy searching for company names and stock symbols.
- Handles errors gracefully and returns appropriate HTTP responses.

### 2. Web Frontend Module (app.py)
- Offers a simple web interface where users can:
  - Input the company name or stock symbol.
  - Specify the year for the CSR report.
- Sends requests to the FastAPI backend and displays the query results on the webpage.
- Handles user input validation and API exceptions.


### 3. Server Management Module (main.py)
- Simultaneously starts both FastAPI and Flask servers:
  - FastAPI serves as the backend API for data queries.
  - Flask serves as the frontend interface for user interaction.
- Uses multithreading to run the FastAPI server and a subprocess to start the Flask server.
- Provides an interactive command-line menu that allows users to:
  1. Open the browser to access the Flask frontend page.
  2. Shut down the servers.

## Project Structure
```
web_search/
├── api.py          # Main FastAPI file, handles API requests
├── app.py          # Main Flask file, handles frontend requests
├── main.py         # Entry point for starting Flask and FastAPI servers
├── templates/
│   └── index.html  # Frontend HTML template
```

## Running Project

### Prerequisites
Before running the project, ensure you have the following:

- Python Version: *Python 3.8* or above is recommended.
- Required Libraries:
  - Flask: For the frontend web framework.
  - FastAPI: For building the backend API.
  - Uvicorn: For running the FastAPI server.
  - psycopg2: PostgreSQL driver for database operations.
  - Requests: For making HTTP requests.
  - Webbrowser: For opening URLs in the default web browser.

Install dependencies:
```bash
pip install -r requirements.txt  # Install dependencies
```

### Configuration
Configure the database:
  - Create a PostgreSQL database.
  - Update the DB_CONFIG settings in the config.py file with your database credentials.

Set the environment variable for the FastAPI API URL (optional):
  ```bash
  export API_URL="http://localhost:8000/report"
  ```

### Usage Instructions

1. Start the Application:
Run the main.py file to start both the FastAPI and Flask servers:
  ```bash
  python ./modulesweb_search/main.py
  ```

2. Access the Application
Open the Web Page
- Type 1 in the terminal and press Enter. This will automatically open the Flask frontend in your default web browser at:
  ```arduino
  http://127.0.0.1:5000
  ```
Close the Servers
- If you want to stop the servers, type 2 in the terminal and press Enter. Both the FastAPI and Flask servers will shut down safely.

3. Use the Web Frontend to Query CSR Reports
- Open the Flask frontend in your browser.
- Fill out the form with the following details:
- Company Name or Stock Symbol: Enter the company name (e.g., "Example Corp") or stock symbol (e.g., "EXM").
  - Year: Enter the year for the CSR report (e.g., "2023").
  - Click the Submit button to send the query.
- The page will display the results, including:
  - Company Name
  - Stock Symbol
  - Report URL (clickable for download)
  - MinIO Storage Path (if applicable)

4. Download and Upload Reports:
If you prefer to directly test the FastAPI backend, you can use the following URL format (replace <company_or_symbol> and <year> with your query parameters):
  ```arduino
  http://127.0.0.1:8000/report?query=<company_or_symbol>&year=<year>
  ```
The FastAPI backend will return the results in JSON format:
- On sucess
  ```json
  [
    {
        "company_name": "Example Corp",
        "symbol": "EXM",
        "report_url": "http://example.com/report.pdf",
        "minio_path": "minio://bucket/report.pdf"
    }
]
  ```
- On failure
  ```json
  [
    {"message": "CSR report not found for the company"}
]
  ```

> - Ensure the PostgreSQL database is running and properly configured before starting the application.
> - MinIO integration is optional and can be used for storing CSR report files.
> - For production deployment, consider using a process manager like gunicorn and a reverse proxy like nginx.

## Code Quality Checks
The project enforces code quality standards using `flake8`, `black`, `isort`, and `bandit`:
```bash
poetry run flake8 ./modules  # Linting
poetry run black --check ./modules  # Formatting check
poetry run isort --check-only ./modules  # Import sorting check
poetry run bandit -r ./modules  # Security scan
```

## Conclusion
This project provides a complete solution for querying and displaying CSR reports, combining a robust FastAPI backend with a user-friendly Flask frontend. It is designed to be modular, scalable, and easy to use, making it suitable for organizations that need to manage and access CSR reports efficiently. By leveraging modern web technologies and a clean architecture, this system can be easily extended to support additional features, such as user authentication, advanced search filters, or integration with other data sources.

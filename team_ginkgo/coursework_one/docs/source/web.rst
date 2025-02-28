=================================
CSR Report Search Application
=================================

This project is a simple **CSR (Corporate Social Responsibility) Report Search Tool** that combines **FastAPI** and **Flask** to provide both backend API services and a web interface. Below is an overview of the project structure and usage guidelines.


Project Structure
------------------------
```
/web_search
    ├── api.py       # FastAPI backend that provides the CSR report query API
    ├── app.py       # Flask frontend for users to search for CSR reports
    └── main.py      # Main script to start both FastAPI and Flask servers
```

---

FastAPI Backend (api.py)
-------------------------------
The **FastAPI backend** handles requests for CSR reports by querying a PostgreSQL database.

**Features**:
- Establishes a connection to a PostgreSQL database.
- Provides an API endpoint `/report` that allows users to search for CSR reports using a **company name or stock symbol** and a **year**.
- Returns company details, stock symbols, report URLs, and MinIO storage paths.

**Example API Request**:
```
GET http://127.0.0.1:8000/report?query=Tesla&year=2023
```

**Example API Response**:
```json
[
    {
        "company_name": "Tesla Inc.",
        "symbol": "TSLA",
        "report_url": "https://example.com/tesla_2023_csr.pdf",
        "minio_path": "/minio/reports/tesla_2023.pdf"
    }
]
```

---

Flask Frontend (app.py)
------------------------------
The **Flask frontend** provides a simple **web interface** that allows users to enter a **company name** and **year** to search for CSR reports.

**How It Works**:
1. The user enters a **company name or stock symbol** and a **year**.
2. The Flask app sends a request to the FastAPI backend.
3. The backend returns CSR report details, which are displayed in the web interface.

---

Main Script (main.py)
----------------------------
The `main.py` script is responsible for **starting both FastAPI and Flask servers simultaneously**.

**How It Works**:
- Runs the **FastAPI server** in a background thread.
- Starts the **Flask server** and waits for it to initialize.
- Provides a simple command-line menu for users to **open the web interface** or **shut down the servers**.

**Available Options**:
```
==========================
 [1] Open Web Page
 [2] Close Server
```

---

How to Run the Application
---------------------------------
To start the application, run:
```
python main.py
```

Once the servers are running, open the **Flask web interface** at:
```
http://127.0.0.1:5000
```

Alternatively, you can access the **FastAPI API** at:
```
http://127.0.0.1:8000/docs
```

---

Requirements
-------------------
Ensure you have the following dependencies installed:
```
pip install fastapi flask uvicorn requests psycopg2
```

---

Conclusion
-----------------
This project provides a **simple and interactive way** to search for CSR reports using a **FastAPI backend** and a **Flask frontend**. It enables users to retrieve reports efficiently and access relevant company information in an organized manner.
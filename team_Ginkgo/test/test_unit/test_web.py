import pytest
import subprocess
import sys
import os
import requests
import time
import threading
import uvicorn
from fastapi.testclient import TestClient

# Dynamically add the path to the source files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules")))

from web_search.api import app as fastapi_app
from web_search.app import app as flask_app

@pytest.fixture(scope="module")
def fastapi_client():
    """Set up a test client for FastAPI."""
    return TestClient(fastapi_app)

@pytest.fixture(scope="module")
def start_flask_server():
    """Start Flask server in a separate thread."""
    def run_flask():
        flask_app.run(port=5000, debug=False, use_reloader=False)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(3)  # Wait for the server to start

def test_fastapi_report_query(fastapi_client):
    """Test querying CSR reports from FastAPI API."""
    response = fastapi_client.get("/report", params={"query": "Apple", "year": 2022})
    assert response.status_code == 200, "❌ FastAPI query failed!"
    assert isinstance(response.json(), list), "❌ Response should be a list of reports"
    print("✅ FastAPI CSR report query successful.")

def test_flask_index_page(start_flask_server):
    """Test if Flask app is serving the index page correctly."""
    response = requests.get("http://127.0.0.1:5000/")
    assert response.status_code == 200, "❌ Flask index page did not load!"
    assert "CSR Report Lookup" in response.text, "❌ Flask page content incorrect!"
    print("✅ Flask index page loaded successfully.")

def test_code_quality():
    """Run linting, formatting, and security scans for api.py, app.py, and main.py."""
    python_exec = sys.executable  # Get the correct Python path
    files_to_check = [
        "../../modules/web_search/api.py",
        "../../modules/web_search/app.py",
        "../../modules/web_search/main.py"
    ]
    for file in files_to_check:
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), file))

        print(f"🔍 Running flake8 on {file}...")
        subprocess.run([python_exec, "-m", "flake8", file_path, "--max-line-length=100"], check=True)

        print(f"🔍 Checking code formatting with black on {file}...")
        subprocess.run([python_exec, "-m", "black", "--check", file_path], check=True)

        print(f"🔍 Sorting imports with isort on {file}...")
        subprocess.run([python_exec, "-m", "isort", "--check-only", file_path], check=True)

        print(f"🔍 Running security scans with Bandit on {file}...")
        subprocess.run([python_exec, "-m", "bandit", "-r", file_path], check=True)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])

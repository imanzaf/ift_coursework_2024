"""
app.py

This module defines a Flask application that provides a web interface to query CSR reports
using a FastAPI backend. The application allows users to input a company name or stock symbol
and a year, and then queries the FastAPI API to retrieve the corresponding CSR report.
"""

from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# FastAPI API address
API_URL = os.getenv("API_URL", "http://localhost:8000/report")

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Handle the root route of the Flask application.

    This function handles both GET and POST requests to the root URL (`/`):
    - For GET requests, it renders the `index.html` template with no result.
    - For POST requests, it processes the form data to query the FastAPI API for CSR reports.

    Args:
        request (flask.request): The request object containing form data.

    Returns:
        flask.Response: The rendered `index.html` template with the query result.
    """
    result = None
    if request.method == "POST":
        company = request.form["company"]
        year = request.form["year"]

        try:
            year = int(year)
        except ValueError:
            return render_template("index.html", result={"message": "Invalid year format, please enter a valid year"})

        # Call FastAPI query API
        try:
            response = requests.get(f"{API_URL}?query={company}&year={year}")
            if response.status_code == 200:
                result = response.json()
            else:
                result = {"message": f"API query failed, error code: {response.status_code}"}
        except requests.exceptions.RequestException:
            result = {"message": "Unable to connect to API server"}

    return render_template("index.html", result=result)

# Run
if __name__ == "__main__":
    """
    Main entry point to start the Flask server.

    This script uses the `app.run` method to start the Flask application
    in debug mode on port `5000`.
    """
    app.run(debug=True, port=5000)

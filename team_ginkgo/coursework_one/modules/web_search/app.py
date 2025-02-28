'''
This is the main file for the web search module. It is a Flask web application that allows users to search for a company's financial report by entering the company name and year. The application will then call the FastAPI API to query the financial report data and display the result on the web page.

The application consists of two main parts:
1. The Flask web application that handles user input and displays the search result.
2. The FastAPI API that queries the financial report data from the database.

Example usage:
- User enters the company name and year in the web application.
- The web application calls the FastAPI API with the user input.
- The FastAPI API queries the financial report data from the database.
- The FastAPI API returns the query result to the web application.
- The web application displays the query result to the user.

'''
from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# FastAPI API address
API_URL = os.getenv("API_URL", "http://localhost:8000/report")


@app.route("/", methods=["GET", "POST"])
def index():
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)

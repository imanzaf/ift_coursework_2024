import sqlite3
from flask import request, jsonify, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import yaml
from flask import Flask
from team_sakura.coursework_one.a_pipeline.modules.db_loader.mongo_db import (
    get_mongo_collection,
)

# Load environment variables from a .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Load configuration from YAML file, using a default path for Docker if not set in environment variables
config_path = os.getenv("CONF_PATH", "a_pipeline/config/conf.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# MongoDB Configuration
mongo_config = config["databaselocal"]

# Connect to MongoDB
client = MongoClient(mongo_config["mongo_uri"])
collection = get_mongo_collection()

# SQLite Database Path
SQLITE_DB_PATH = mongo_config["sqlite_path"]


def get_company_names():
    """
    Fetch unique company names from the SQLite database.

    Returns:
        list[str]: A list of unique company names.
    """
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT security FROM equity_static"
    )  # Adjust table name if necessary
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()
    return companies


@app.route("/get_companies", methods=["GET"])
def get_companies():
    """
    Return a list of unique company names from the SQLite database.

    Returns:
        JSON response containing a list of company names.
    """
    return jsonify(get_company_names())


@app.route("/csr_reports", methods=["GET"])
def get_csr_reports():
    """
    Fetch CSR reports based on query parameters (company_name and/or report_year).

    Query Parameters:
        company_name (str, optional): Filter by company name (case-insensitive).
        year (str, optional): Filter by report year.

    Returns:
        JSON response containing a list of CSR reports.
    """
    company_name = request.args.get("company_name")
    report_year = request.args.get("year")

    query = {}
    if company_name:
        query["company_name"] = {
            "$regex": company_name,
            "$options": "i",
        }  # Case-insensitive search
    if report_year:
        query["report_year"] = report_year

    reports = list(
        collection.find(
            query,
            {
                "_id": 0,
                "company_name": 1,
                "report_year": 1,
                "pdf_link": 1,
                "minio_url": 1,
            },
        )
    )
    return jsonify(reports)  # Returns only PDF URLs instead of full report details


@app.route("/")
def index():
    """
    Render the main filter page.

    Returns:
        HTML page with a filtering UI.
    """
    return render_template("filter.html")


if __name__ == "__main__":
    # Run the Flask application in debug mode
    app.run(debug=True)

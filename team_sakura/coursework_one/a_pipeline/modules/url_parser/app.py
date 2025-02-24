import sqlite3
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import yaml
from team_sakura.coursework_one.a_pipeline.modules.db_loader.mongo_db import get_mongo_collection

load_dotenv()

app = Flask(__name__)


# Get the current working directory or the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config', 'conf.yaml')

# Load config file
try:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Config file not found at {config_path}. Please ensure it's in the correct directory.")
    raise


# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
collection = get_mongo_collection()

# SQLite Connection
SQLITE_DB_PATH = "/Users/estheragossa/PycharmProjects/ift_coursework_2024/000.Database/SQL/Equity.db"

def get_company_names():
    """Fetch unique company names from equity.db."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT security FROM equity_static")  # Adjust table name if needed
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()
    return companies

@app.route("/get_companies", methods=["GET"])
def get_companies():
    """Return a list of company names from the SQLite database."""
    return jsonify(get_company_names())

@app.route("/csr_reports", methods=["GET"])
def get_csr_reports():
    """Fetch CSR reports based on query parameters (company_name and/or year)."""
    company_name = request.args.get("company_name")
    report_year = request.args.get("year")

    query = {}
    if company_name:
        query["company_name"] = {"$regex": company_name, "$options": "i"}  # Case-insensitive search
    if report_year:
        query["report_year"] = report_year

    reports = list(collection.find(query, {"_id": 0, "company_name": 1, "report_year": 1, "pdf_link": 1, "minio_url": 1}))
    return jsonify(reports)  # Returns PDF URLs instead of report details

@app.route("/")
def index():
    """Render the main filter page."""
    return render_template("filter.html")

if __name__ == "__main__":
    app.run(debug=True)

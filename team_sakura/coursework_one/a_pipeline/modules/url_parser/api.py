from fastapi import FastAPI, Query
from pymongo import MongoClient
import yaml
import os

# Load configuration from YAML file, using a default path for Docker if not set in environment variables
config_path = os.getenv("CONF_PATH", "a_pipeline/config/conf.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# MongoDB Configuration
mongo_config = config["databaselocal"]

# Connect to MongoDB
MONGO_CLIENT = MongoClient(mongo_config["mongo_uri"])
db = MONGO_CLIENT[mongo_config["mongo_db"]]
collection = db[mongo_config["mongo_collection"]]

# Initialize FastAPI application
app = FastAPI()


@app.get("/reports")
def get_reports(
    company_name: str = Query(None, description="Filter by company name"),
    year: int = Query(None, description="Filter by report year"),
    sector: str = Query(None, description="Filter by GICS sector"),
    industry: str = Query(None, description="Filter by GICS industry"),
    country: str = Query(None, description="Filter by country"),
    region: str = Query(None, description="Filter by region"),
):
    """
    Retrieve CSR reports based on multiple filter criteria.

    Query Parameters:
        company_name (str, optional): Filter by company name (case-insensitive).
        year (int, optional): Filter by report year.
        sector (str, optional): Filter by GICS sector (case-insensitive).
        industry (str, optional): Filter by GICS industry (case-insensitive).
        country (str, optional): Filter by country (case-insensitive).
        region (str, optional): Filter by region (case-insensitive).

    Returns:
        dict: JSON response containing count and a list of matching reports.
    """
    query = {}

    if company_name:
        query["company_name"] = {"$regex": company_name, "$options": "i"}  # Case-insensitive search
    if year:
        query["report_year"] = year
    if sector:
        query["gics_sector"] = {"$regex": sector, "$options": "i"}
    if industry:
        query["gics_industry"] = {"$regex": industry, "$options": "i"}
    if country:
        query["country"] = {"$regex": country, "$options": "i"}
    if region:
        query["region"] = {"$regex": region, "$options": "i"}

    # Fetch matching documents and exclude MongoDB's default _id field
    results = list(collection.find(query, {"_id": 0}))

    # Normalize company name for consistent storage, if provided
    if company_name:
        collection.update_many({}, {"$set": {"company_name": company_name.lower()}})
    else:
        print("Error: company_name is None")

    return {"count": len(results), "reports": results}


if __name__ == "__main__":
    import uvicorn

    # Run FastAPI application using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

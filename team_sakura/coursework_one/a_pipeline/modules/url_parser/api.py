from fastapi import FastAPI, Query
from pymongo import MongoClient
import yaml
import os
# Load config

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


# MongoDB connection
MONGO_CLIENT = MongoClient(config["database"]["mongo_uri"])
db = MONGO_CLIENT[config["database"]["mongo_db"]]
collection = db[config["database"]["mongo_collection"]]

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
    """Retrieve CSR reports based on filters"""
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

    results = list(collection.find(query, {"_id": 0}))  # Exclude MongoDB's default _id field
    collection.update_many({}, {"$set": {"company_name": company_name.lower()}})
    return {"count": len(results), "reports": results}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

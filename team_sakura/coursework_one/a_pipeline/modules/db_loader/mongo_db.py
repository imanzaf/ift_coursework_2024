import yaml
from pymongo import MongoClient
import os


# Get the current working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config', 'conf.yaml')

# Load config file
try:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Config file not found at {config_path}. Please ensure it's in the correct directory.")
    raise

### MongoDB Connection ###
def get_mongo_collection():
    MONGO_CLIENT = MongoClient(config["database"]["mongo_uri"])
    db = MONGO_CLIENT[config["database"]["mongo_db"]]
    collection = db[config["database"]["mongo_collection"]]
    collection.create_index([("company_name", 1)])
    collection.create_index([("report_year", 1)])
    return collection

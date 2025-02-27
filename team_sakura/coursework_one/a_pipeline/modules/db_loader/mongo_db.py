import yaml
from pymongo import MongoClient
import os

config_path = os.getenv("CONF_PATH", "/app/config/conf.yaml")  # Default path for Docker
with open(config_path, "r") as file:
    config = yaml.safe_load(file)



### MongoDB Connection ###
def get_mongo_collection():
    MONGO_CLIENT = MongoClient(config["database"]["mongo_uri"])
    db = MONGO_CLIENT[config["database"]["mongo_db"]]
    collection = db[config["database"]["mongo_collection"]]
    collection.create_index([("company_name", 1)])
    collection.create_index([("report_year", 1)])
    return collection


def delete_all_documents_from_mongo():
    collection = get_mongo_collection()
    try:
        # Delete all documents in the collection
        result = collection.delete_many({})
        print(f"Deleted {result.deleted_count} documents from MongoDB.")
    except Exception as e:
        print(f"Error while deleting from MongoDB: {e}")


# delete_all_documents_from_mongo() Call the function to delete all documents from MongoDB

import yaml
from pymongo import MongoClient
import os

# Load configuration from YAML file, using a default path for Docker if not set in environment variables
config_path = os.getenv("CONF_PATH", "a_pipeline/config/conf.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# Determine MongoDB configuration based on environment (Docker or local)
if os.getenv("DOCKER_ENV"):
    mongo_config = config["databasedocker"]
else:
    mongo_config = config["databaselocal"]


def get_mongo_collection():
    """
    Establish a connection to MongoDB and return the specified collection.

    Returns:
        pymongo.collection.Collection: The MongoDB collection object.
    """
    mongo_client = MongoClient(mongo_config["mongo_uri"])
    db = mongo_client[mongo_config["mongo_db"]]
    collection = db[mongo_config["mongo_collection"]]

    # Create indexes to optimize queries on `company_name` and `report_year`
    collection.create_index([("company_name", 1)])
    collection.create_index([("report_year", 1)])

    return collection


def delete_all_documents_from_mongo():
    """
    Deletes all documents from the specified MongoDB collection.
    """
    collection = get_mongo_collection()
    try:
        # Delete all documents in the collection
        result = collection.delete_many({})
        print(f"Deleted {result.deleted_count} documents from MongoDB.")
    except Exception as e:
        print(f"Error while deleting from MongoDB: {e}")


# Call delete_all_documents_from_mongo() to remove all documents from MongoDB when needed

import yaml
from pymongo import MongoClient


# Load configuration
with open("/Users/estheragossa/PycharmProjects/ift_coursework_2024/team_sakura/coursework_one/a_pipeline/config/conf.yaml", "r") as file:
    config = yaml.safe_load(file)

### MongoDB Connection ###
def get_mongo_collection():
    MONGO_CLIENT = MongoClient(config["database"]["mongo_uri"])
    db = MONGO_CLIENT[config["database"]["mongo_db"]]
    collection = db[config["database"]["mongo_collection"]]
    collection.create_index([("company_name", 1)])
    collection.create_index([("report_year", 1)])
    return collection

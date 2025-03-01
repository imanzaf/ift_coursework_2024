import json
import os.path

from flask.cli import load_dotenv
from imageio.testing import ROOT_DIR
from pymongo import MongoClient, errors
import datetime
import sqlite3
import pandas as pd
import dotenv
from ...modules.utils.dockercheck import is_running_in_docker
load_dotenv()

if is_running_in_docker():
    ROOT_DIR = os.getenv("ROOT_DIR_DOCKER")
else:
    ROOT_DIR = os.getenv("ROOT_DIR_LOCAL")

class CompanyData:
    """
    A class representing a company's data.
    """

    def __init__(self, symbol, security, gics_sector, gics_industry, country, region, website_url=None, csr_reports=None):
        self.symbol = symbol
        self.security = security
        self.gics_sector = gics_sector
        self.gics_industry = gics_industry
        self.country = country
        self.region = region

        self.website_url = website_url
        self.csr_reports = csr_reports if csr_reports else {}
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "symbol": self.symbol,
            "security": self.security,
            "gics_sector": self.gics_sector,
            "gics_industry": self.gics_industry,
            "country": self.country,
            "region": self.region,
            "website_url": self.website_url,
            "csr_reports": self.csr_reports,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
class CompanyDatabase:
    """
    A class to handle database operations for CompanyData.
    """

    def __init__(self, db):
        """
        Initialize the CompanyDatabase with a MongoDB connection.
        :param db: MongoDB database instance.
        """
        self.collection = db["companies"]  # MongoDB collection

    def add_company(self, company):
        """
        Add a new company to the database.
        :param company: CompanyData object
        """
        if self.collection.find_one({"symbol": company.symbol}):
            print(f"⚠️ Company with symbol {company.symbol} already exists!")
            return
        self.collection.insert_one(company.to_dict())
        print(f"✅ Company {company.security} added!")

    def add_csr_report(self, symbol, report_link):
        """
        Add a CSR report link to an existing company.
        :param symbol: Ticker symbol of the company.
        :param report_link: URL of the CSR report.
        """
        result = self.collection.update_one(
            {"symbol": symbol},
            {
                "$push": {"csr_reports": report_link},  # Append to array
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
        )
        if result.modified_count > 0:
            print(f"✅ CSR Report added for {symbol}")
        else:
            print(f"⚠️ No company found with symbol {symbol}")

    def get_company(self, symbol):
        """
        Retrieve a company's details by symbol.
        :param symbol: Ticker symbol of the company.
        :return: CompanyData object or None if not found.
        """
        company_doc = self.collection.find_one({"symbol": symbol}, {"_id": 0})
        if company_doc:
            return CompanyData(**company_doc)
        else:
            print(f"⚠️ No company found with symbol {symbol}")
            return None

    def update_gics_sector(self, symbol, new_gics_sector):
        """
        Update the gics_sector of a company.
        :param symbol: Ticker symbol of the company.
        :param new_gics_sector: New gics_sector security.
        """
        result = self.collection.update_one(
            {"symbol": symbol},
            {
                "$set": {"gics_sector": new_gics_sector, "updated_at": datetime.datetime.utcnow()}
            }
        )
        if result.modified_count > 0:
            print(f"✅ gics_sector updated for {symbol}")
        else:
            print(f"⚠️ No company found with symbol {symbol}")

    def delete_company(self, symbol):
        """
        Delete a company from the database.
        :param symbol: Ticker symbol of the company.
        """
        result = self.collection.delete_one({"symbol": symbol})
        if result.deleted_count > 0:
            print(f"✅ Company with symbol {symbol} deleted!")
        else:
            print(f"⚠️ No company found with symbol {symbol}")

# --- MongoDB Connection Setup ---
def connect_to_mongo():
    try:
        # MongoDB Connection URI
        if is_running_in_docker():
            mongo_uri = "mongodb://mongo_db_cw:27017"
        else:
            mongo_uri = "mongodb://localhost:27019"

        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        # Attempt to connect to MongoDB
        mongo_client.server_info()  # Will raise an exception if can't connect
        print("✅ Connected to MongoDB!")
        return mongo_client
    except errors.ServerSelectionTimeoutError as err:
        print(f"❌ Error: Unable to connect to MongoDB - {err}")
        return None


def load_sql_to_pandas():


    # Debugging: Check if ROOT_DIR is set correctly
    if is_running_in_docker():
        ROOT_DIR = os.getenv("ROOT_DIR_DOCKER")
    else:
        ROOT_DIR = os.getenv("ROOT_DIR_LOCAL")
        
    if ROOT_DIR is None:
        raise ValueError("ROOT_DIR is not set. Check your .env file.")

    db_path = os.path.join(ROOT_DIR, "000.Database", "SQL", "Equity.db")

    # Debugging: Print file path
    print(f"Trying to connect to database at: {db_path}")

    # Debugging: Check if file exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file NOT found at: {db_path}")

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)

    # Read the table into a Pandas DataFrame
    query = "SELECT * FROM equity_static"  # Adjust if the table security differs
    df = pd.read_sql_query(query, conn)

    # Close the connection
    conn.close()

    # Display DataFrame
    print(df.head())
    return df


def create_mongo_seed_file(df):
    """Convert DataFrame to JSON and save for MongoDB import inside 'mongo_seed/' folder."""

    # Define folder and file path
    seed_folder = os.path.join(ROOT_DIR, "team_adansonia/coursework_one/mongo-seed")
    seed_file = os.path.join(seed_folder, "seed_data.json")

    # Check if file already exists
    if os.path.exists(seed_file):
        print(f"⚠️ Seed file already exists: {seed_file} (Skipping generation)")
        return seed_file  # Return existing file path
    company_list = [CompanyData(**row).to_dict() for row in df.to_dict(orient="records")]

    # Save to JSON
    with open(seed_file, "w", encoding="utf-8") as f:
        json.dump(company_list, f, indent=4)

    print(f"✅ MongoDB seed file saved to {seed_file}")
    # Ensure the 'mongo_seed' folder exists
    os.makedirs(seed_folder, exist_ok=True)


def reset_database():
    confirmation = input("Are you sure you want to reset the database? Yes/No: ").strip().lower()
    if confirmation != "yes":
        print("❌ Database reset aborted.")
        return

    mongo_client = connect_to_mongo()
    if mongo_client:
        db = mongo_client["csr_reports"]
        db.companies.drop()  # Drops the 'companies' collection
        print("✅ Database reset: 'companies' collection dropped.")

        # Re-import the seed data
        import_seed_to_mongo()
        print("✅ Seed data imported successfully.")

        # **Explicitly reset csr_reports to empty dictionary**
        db.companies.update_many({}, {"$set": {"csr_reports": {}}})
        print("✅ csr_reports field reset to empty dictionary for all records.")


def import_seed_to_mongo():
    """Automatically import the seed data from the generated JSON file into MongoDB."""
    # Step 1: Connect to MongoDB
    mongo_client = connect_to_mongo()  # Connect to MongoDB
    if mongo_client is None:
        return  # Exit if MongoDB connection failed

    db = mongo_client["csr_reports"]  # Access the MongoDB database
    collection = db["companies"]  # Access the "companies" collection

    # Step 2: Delete all existing documents in the collection
    collection.delete_many({})  # Removes all documents in the collection
    print("⚠️ All existing documents in the collection have been deleted.")

    # Step 3: Load the seed file into MongoDB
    seed_file = os.path.join(ROOT_DIR, "team_adansonia/coursework_one/mongo-seed", "seed_data.json")
    if os.path.exists(seed_file):  # Check if the seed file exists
        with open(seed_file, "r") as f:
            try:
                companies = json.load(f)  # Read JSON data from the seed file
                if isinstance(companies, list):  # Ensure the data is a list of documents
                    collection.insert_many(companies)  # Insert data into MongoDB
                    print(f"✅ Seed data successfully imported into MongoDB!")
                else:
                    print(f"⚠️ Seed data should be a list of documents, found {type(companies)}.")
            except json.JSONDecodeError as e:
                print(f"⚠️ Error reading the seed file: {e}")
            except Exception as e:
                print(f"⚠️ An error occurred while importing seed data: {e}")
    else:
        print(f"⚠️ Seed file not found: {seed_file}")

    return collection
# --- Main Function for Testing ---
def main():
    df = load_sql_to_pandas()
    create_mongo_seed_file(df)
    mongo_client = connect_to_mongo()
    import_seed_to_mongo()

    if mongo_client is None:
        return  # If MongoDB is not connected, terminate the program

    # Access the database (not the collection directly)
    db = mongo_client["csr_reports"]

#run main on import 
main()

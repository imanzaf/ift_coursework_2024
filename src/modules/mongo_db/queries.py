from pymongo import MongoClient
from src.modules.mongo_db.company_data import CompanyDatabase


def connect_to_mongo():
    try:
        mongo_uri = "mongodb://localhost:27019/"
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()
        print("✅ Connected to MongoDB!")
        return mongo_client
    except Exception as err:
        print(f"❌ Error: Unable to connect to MongoDB - {err}")
        return None


def search_by_name(company_db, name):
    """Search for companies by name."""
    results = company_db.collection.find({"security": {"$regex": name, "$options": "i"}}, {"_id": 0})
    return list(results)


def search_by_sector(company_db, sector):
    """Search for companies by sector."""
    results = company_db.collection.find({"gics_sector": {"$regex": sector, "$options": "i"}}, {"_id": 0})
    return list(results)


def search_by_csr_report(company_db):
    """Find companies that have CSR reports."""
    results = company_db.collection.find({"csr_reports": {"$ne": []}}, {"_id": 0})
    return list(results)


def search_by_website(company_db, website_url):
    """Find a company by its website URL."""
    results = company_db.collection.find({"website_url": website_url}, {"_id": 0})
    return list(results)


def main():
    mongo_client = connect_to_mongo()
    if mongo_client is None:
        return

    db = mongo_client["csr_reports"]
    company_db = CompanyDatabase(db)

    while True:
        print("\n🔍 Company Search Menu:")
        print("1. Search by company name")
        print("2. Search by sector")
        print("3. Search for companies with CSR reports")
        print("4. Search by website URL")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            name = input("Enter company name: ")
            results = search_by_name(company_db, name)
            print(results)
        elif choice == "2":
            sector = input("Enter sector: ")
            results = search_by_sector(company_db, sector)
            print(results)
        elif choice == "3":
            results = search_by_csr_report(company_db)
            print(results)
        elif choice == "4":
            website_url = input("Enter website URL: ")
            results = search_by_website(company_db, website_url)
            print(results)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()

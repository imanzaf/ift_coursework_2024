from pymongo import MongoClient
from team_adansonia.coursework_one.a_link_retrieval.modules.mongo_db.company_data import CompanyDatabase


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
    return results


def search_by_sector(company_db, sector):
    """Search for companies by sector."""
    results = company_db.collection.find({"gics_sector": {"$regex": sector, "$options": "i"}}, {"_id": 0})
    return results


def get_crs_report_link(csr_reports, year):
    # Look for the specific year in the csr_reports dictionary
    return csr_reports.get(str(year), None)


def get_company_info(company_db, company_name, year):
    # Search for the company by name in the database
    company_data = list(search_by_name(company_db, company_name))

    # Check if data was found
    if company_data:
        # Assuming we only expect one company, get the first result
        company_data = company_data[0]

        company_symbol = company_data.get('symbol', 'Not Available')

        # Retrieve the Minio link if available (only if 'minio_urls' exists)
        minio_url = company_data.get('minio_urls', None)

        # Retrieve the CRS report link if available for the given year
        csr_report_link = get_crs_report_link(company_data.get('csr_reports', {}), year)

        return {
            'Company Name': company_name,
            'Symbol': company_symbol,
            'Minio Link': minio_url if minio_url else 'Not Available',
            'CRS Report Link': csr_report_link if csr_report_link else 'Not Available'
        }
    else:
        return f"No data found for {company_name} in {year}."

def main():
    mongo_client = connect_to_mongo()
    if mongo_client is None:
        return

    db = mongo_client["csr_reports"]
    company_db = CompanyDatabase(db)

    while True:
        print("\n🔍 Company Search Menu:")
        print("0. Search by company name for given year")
        print("1. Search by company name")
        print("2. Search by sector")
        print("3. Exit")

        choice = input("Enter your choice: ")
        if choice == "0":
            company_name = input("Enter company name: ")
            year = input("Enter company year: ")
            results = get_company_info(company_db, company_name, year)
            print(results)
        elif choice == "1":
            name = input("Enter company name: ")
            results = search_by_name(company_db, name)
            print(list(results))
        elif choice == "2":
            sector = input("Enter sector: ")
            results = search_by_sector(company_db, sector)
            print(list(results))
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()

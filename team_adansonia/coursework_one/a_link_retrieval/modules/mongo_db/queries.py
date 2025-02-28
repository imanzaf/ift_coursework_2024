from pymongo import MongoClient

from team_adansonia.coursework_one.a_link_retrieval.modules.mongo_db.company_data import CompanyDatabase
from modules.utils.dockercheck import is_running_in_docker


def connect_to_mongo():
    try:
        if is_running_in_docker():
            mongo_uri = "mongodb://mongo_db_cw:27017"
        else:
            mongo_uri = "mongodb://localhost:27019"

        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()
        print("✅ Connected to MongoDB!")
        return mongo_client
    except Exception as err:
        print(f"❌ Error: Unable to connect to MongoDB - {err}")
        return None


def search_by_name(company_db, name):
    """Search for companies by name."""
    results = company_db.find({"security": {"$regex": name, "$options": "i"}}, {"_id": 0})
    return results


def search_by_sector(company_db, sector):
    """Search for companies by sector."""
    results = company_db.find({"gics_sector": {"$regex": sector, "$options": "i"}}, {"_id": 0})
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



def add_company(collection):
    """Add a new company to the database."""
    symbol = input("Enter company symbol: ")
    security = input("Enter company security name: ")
    gics_sector = input("Enter GICS sector: ")
    gics_industry = input("Enter GICS industry: ")
    country = input("Enter country: ")
    region = input("Enter region: ")
    website_url = {}
    csr_reports = {}
    # You can expand this as per your needs

    company = CompanyData(
        symbol=symbol,
        security=security,
        gics_sector=gics_sector,
        gics_industry=gics_industry,
        country=country,
        region=region,
        website_url=website_url if website_url else None,
        csr_reports=csr_reports
    )
    company = company.to_dict()

    if collection.find_one({"symbol": company["symbol"]}):
        print(f"⚠️ Company with symbol "+  company["symbol"] +" already exists!")
        return
    collection.insert_one(company)
    print(f"✅ Company added")

def delete_company_from_db(collection):
    symbol = input("Enter the symbol of the company you want to delete: ")

    # Try to delete the company
    result = collection.delete_one({"symbol": symbol})

    if result.deleted_count > 0:
        print(f"✅ Company with symbol {symbol} deleted!")
    else:
        print(f"⚠️ No company found with symbol {symbol}")

def main():
    mongo_client = connect_to_mongo()
    if mongo_client is None:
        return

    db = mongo_client["csr_reports"]
    collection = db.companies
    while True:
        print("\n🔍 Company Search Menu:")
        print("0. Search by company name for given year")
        print("1. Search by company name")
        print("2. Search by sector")
        print("3. Add Company")
        print("4. Delete Company")
        print("5. Exit")

        choice = input("Enter your choice: ")
        if choice == "0":
            company_name = input("Enter company name: ")
            year = input("Enter company year: ")
            results = get_company_info(collection, company_name, year)
            print(results)
        elif choice == "1":
            name = input("Enter company name: ")
            results = search_by_name(collection, name)
            print(list(results))
        elif choice == "2":
            sector = input("Enter sector: ")
            results = search_by_sector(collection, sector)
            print(list(results))
        elif choice == "3":
            add_company(collection)
        elif choice == "4":
            delete_company_from_db(collection)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")

#poetry run python -m team_adansonia.coursework_one.a_link_retrieval.modules.mongo_db.queries
if __name__ == "__main__":
    main()

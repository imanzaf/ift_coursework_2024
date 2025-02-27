import json
import psycopg2
import re
from pathlib import Path

# JSON file path
# Get the absolute path of the script file
script_dir = Path(__file__).resolve().parent
print(f"Script directory: {script_dir}")

# Construct the path to the data file
json_file_path = script_dir / "../../../team_jacaranda/coursework_one/static/company_pdf_links.json"
# Resolve the path (remove redundant ../)
json_file_path = json_file_path.resolve()
print(f"JSON file path: {json_file_path}")

# Read the JSON file
with open(json_file_path, "r") as file:
    data = json.load(file)
print("JSON file read successfully")

# PostgreSQL database connection configuration
db_config = {
    "dbname": "fift",
    "user": "postgres",
    "password": "postgres",
    "host": "host.docker.internal",
    "port": 5439
}

# Year extraction function with improved regex
def extract_year(url):
    # List of regex patterns to match different year formats in URLs
    patterns = [
        r"(\d{4})\.pdf$",                  # Matches URLs ending with "2022.pdf"
        r"_(\d{4})_",                      # Matches URLs with "_2022_" in the middle
        r"(\d{4})/[^/]+\.pdf$",            # Matches URLs with "2022/" before the file name
        r"([1-2][0-9]{3})"                 # General year pattern in the URL
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return int(match.group(1))

    return None

# Connect to the PostgreSQL database
try:
    print("Connecting to the PostgreSQL database...")
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    print("Connected to the database")

    # Iterate through the JSON data
    for company_name, urls in data.items():
        # Check if the company name exists in the company_static table
        cursor.execute("SELECT security FROM csr_reporting.company_static WHERE security = %s", (company_name,))
        result = cursor.fetchone()

        if result:
            # If the company exists, insert URL data
            for url in urls:
                # Extract the year from the URL
                report_year = extract_year(url)

                # Insert data into the company_reports table
                insert_query = """
                    INSERT INTO csr_reporting.company_reports (security, report_url, report_year)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (company_name, url, report_year))

    # Commit the transaction
    conn.commit()
    print("Transaction committed successfully")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the database connection
    if conn:
        cursor.close()
        conn.close()
        print("Database connection closed")

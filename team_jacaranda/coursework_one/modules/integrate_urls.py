import json
import psycopg2
import re
from pathlib import Path

# JSON file path
# Get the absolute path of the script file
script_dir = Path(__file__).resolve().parent
# Construct the path to the data file
json_file_path = script_dir / "../../../team_jacaranda/coursework_one/static/company_pdf_links.json"
# Resolve the path (remove redundant ../)
json_file_path = json_file_path.resolve()

# Read the JSON file
with open(json_file_path, "r") as file:
    data = json.load(file)

# PostgreSQL database connection configuration
db_config = {
    "dbname": "fift",
    "user": "postgres",
    "password": "postgres",
    "host": "host.docker.internal",
    "port": 5439
}

# Connect to the PostgreSQL database
try:
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Iterate through the JSON data
    for company_name, urls in data.items():
        # Check if the company name exists in the company_static table
        cursor.execute("SELECT security FROM csr_reporting.company_static WHERE security = %s", (company_name,))
        result = cursor.fetchone()

        if result:
            # If the company exists, insert URL data
            for url in urls:
                # Extract the year from the URL
                year_match = re.search(r"(\d{4})\.pdf$", url)
                report_year = int(year_match.group(1)) if year_match else None

                # Insert data into the company_reports table
                insert_query = """
                    INSERT INTO csr_reporting.company_reports (security, report_url, report_year)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (company_name, url, report_year))

    # Commit the transaction
    conn.commit()
    print("Data inserted successfully!")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the database connection
    if conn:
        cursor.close()
        conn.close()

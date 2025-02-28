import sqlite3
import yaml
import os

# Load configuration from YAML file, using a default path for Docker if not set in environment variables
config_path = os.getenv("CONF_PATH", "a_pipeline/config/conf.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# Determine database path based on environment (Docker or local)
if os.getenv("DOCKER_ENV"):
    DB_PATH = config["databasedocker"]["sqlite_path"]
else:
    DB_PATH = config["databaselocal"]["sqlite_path"]


def fetch_companies():
    """
    Fetch company data from the SQLite database.

    Returns:
        list[dict]: A list of dictionaries containing company information.
    """
    conn = sqlite3.connect(DB_PATH)
    print("Using database:", DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT security, symbol, gics_sector, gics_industry, country, region FROM equity_static
        """
    )

    companies = [
        {
            "company_name": row[0],
            "symbol": row[1],
            "gics_sector": row[2],
            "gics_industry": row[3],
            "country": row[4],
            "region": row[5],
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return companies  # Ensure database connection is closed before returning results

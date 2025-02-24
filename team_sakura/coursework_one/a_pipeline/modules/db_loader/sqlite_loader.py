import sqlite3
import yaml
import os

# Get the current working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config', 'conf.yaml')

# Load config file
try:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Config file not found at {config_path}. Please ensure it's in the correct directory.")
    raise

DB_PATH = config["database"]["sqlite_path"]

def fetch_companies():
    """Fetch company data from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT security, symbol, gics_sector, gics_industry, country, region 
        FROM equity_static
    """)

    companies = [
        {
            "company_name": row[0],
            "symbol": row[1],
            "gics_sector": row[2],
            "gics_industry": row[3],
            "country": row[4],
            "region": row[5]
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return companies

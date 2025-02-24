import sqlite3
import yaml

# Load config
with open("/Users/estheragossa/PycharmProjects/ift_coursework_2024/team_sakura/coursework_one/a_pipeline/config/conf.yaml", "r") as file:
    config = yaml.safe_load(file)

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

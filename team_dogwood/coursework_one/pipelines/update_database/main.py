"""
manage_companies/main.py

This script provides a command-line interface (CLI) to manage companies in
the `csr_reporting.company_static` table within the `fift` database.

Usage Examples:
  1. Add a new company:
     poetry run python pipelines/manage_companies/main.py add \
       --symbol AAPL \
       --security "Apple Inc." \
       --gics_sector "Information Technology" \
       --gics_industry "Consumer Electronics" \
       --country "USA" \
       --region "North America"

  2. Remove a company:
     poetry run python pipelines/manage_companies/main.py remove --symbol AAPL

  3. List all companies:
     poetry run python pipelines/manage_companies/main.py list
"""

import argparse
import os
import sys

from loguru import logger

# Ensure Python can find your 'src' folder.
# Adjust the path if your project structure differs.
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.database.postgres import PostgreSQLDB


def add_company(db: PostgreSQLDB, args: argparse.Namespace):
    """
    Adds a new company to the `csr_reporting.company_static` table.
    If the symbol already exists, no duplicate is inserted (ON CONFLICT DO NOTHING).
    """
    insert_query = """
    INSERT INTO csr_reporting.company_static
        (symbol, security, gics_sector, gics_industry, country, region)
    VALUES
        (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (symbol) DO NOTHING
    """
    db.execute(
        insert_query,
        (
            args.symbol,
            args.security,
            args.gics_sector,
            args.gics_industry,
            args.country,
            args.region,
        ),
    )
    logger.info(f"Company '{args.symbol}' added successfully.")


def remove_company(db: PostgreSQLDB, args: argparse.Namespace):
    """
    Removes a company from the `csr_reporting.company_static` table
    based on its symbol.
    """
    delete_query = """
    DELETE FROM csr_reporting.company_static
    WHERE symbol = %s
    """
    db.execute(delete_query, (args.symbol,))
    logger.info(f"Company '{args.symbol}' removed successfully.")


def list_companies(db: PostgreSQLDB):
    """
    Lists all companies from the `csr_reporting.company_static` table.
    """
    select_query = """
    SELECT symbol, security, gics_sector, gics_industry, country, region
    FROM csr_reporting.company_static
    ORDER BY symbol
    """
    results = db.fetch(select_query)

    if not results:
        logger.info("No companies found in company_static.")
        return

    logger.info("=== Companies in company_static ===")
    for row in results:
        # row is a dictionary: {'symbol': 'AAPL', 'security': 'Apple Inc.', ...}
        logger.info(
            f"Symbol: {row['symbol']}, "
            f"Security: {row['security']}, "
            f"GICS Sector: {row['gics_sector']}, "
            f"GICS Industry: {row['gics_industry']}, "
            f"Country: {row['country']}, "
            f"Region: {row['region']}"
        )


def main():
    """
    Main function to parse arguments and execute commands.
    """
    parser = argparse.ArgumentParser(
        description="CLI to manage companies in csr_reporting.company_static."
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Sub-command: add
    add_parser = subparsers.add_parser("add", help="Add a new company.")
    add_parser.add_argument(
        "--symbol", required=True, help="Stock symbol (e.g., AAPL)."
    )
    add_parser.add_argument(
        "--security", required=True, help="Company name (e.g., Apple Inc.)."
    )
    add_parser.add_argument(
        "--gics_sector", default="", help="GICS Sector (e.g., Technology)."
    )
    add_parser.add_argument(
        "--gics_industry",
        default="",
        help="GICS Industry (e.g., Consumer Electronics).",
    )
    add_parser.add_argument("--country", default="", help="Country (e.g., USA).")
    add_parser.add_argument(
        "--region", default="", help="Region (e.g., North America)."
    )

    # Sub-command: remove
    remove_parser = subparsers.add_parser("remove", help="Remove an existing company.")
    remove_parser.add_argument(
        "--symbol", required=True, help="Stock symbol to remove."
    )

    # Sub-command: list
    subparsers.add_parser("list", help="List all companies.")

    # Parse the command-line arguments
    args = parser.parse_args()

    # If no sub-command is provided, show help and exit
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Use the database context
    with PostgreSQLDB() as db:
        if args.command == "add":
            add_company(db, args)
        elif args.command == "remove":
            remove_company(db, args)
        elif args.command == "list":
            list_companies(db)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()

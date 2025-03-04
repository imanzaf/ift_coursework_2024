import argparse
import logging
import sys
import os

# ======================================
# 1. Attempt imports from your modules
# ======================================
try:
    from modules.scraper.csr_scraper import main as run_scraper
except ImportError:
    run_scraper = None

try:
    from modules.api.analysis_pipeline import run_analysis
except ImportError:
    run_analysis = None

try:
    from modules.scraper.csr_fix_and_cleanup import main as run_fix_and_cleanup
except ImportError:
    run_fix_and_cleanup = None

try:
    from modules.api.mongo_index_setup import setup_indexes
except ImportError:
    setup_indexes = None

try:
    from modules.api.fastapi_api import app as fastapi_app
except ImportError:
    fastapi_app = None

import uvicorn

# ======================================
# 2. Logging Configuration
# ======================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ======================================
# 3. Argument Parsing
# ======================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Main entry point for the CSR data pipeline."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 3.1 Subcommand: scrape
    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Run the CSR scraper pipeline (fetch new PDF reports, store in MinIO & MongoDB)."
    )
    scrape_parser.add_argument(
        "--max-companies",
        type=int,
        default=None,
        help="Limit the number of companies to scrape (optional)."
    )

    '''
    # 3.2 Subcommand: analysis
    analysis_parser = subparsers.add_parser(
        "analysis",
        help="Run data analysis tasks, e.g., text extraction or sentiment analysis."
    )
    analysis_parser.add_argument(
        "--quick",
        action="store_true",
        help="Use a quick mode, skip heavier tasks."
    )
    '''

    # 3.3 Subcommand: fix
    fix_parser = subparsers.add_parser(
        "fix",
        help="Run the fix/cleanup script for correcting years, removing duplicates, etc."
    )
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making database changes."
    )

    # 3.4 Subcommand: index
    index_parser = subparsers.add_parser(
        "index",
        help="Create or update MongoDB indexes."
    )

    # 3.5 Subcommand: api
    api_parser = subparsers.add_parser(
        "api",
        help="Launch the FastAPI server for CSR data retrieval."
    )
    api_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the API (default: 0.0.0.0)."
    )
    api_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the API (default: 8000)."
    )
    api_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable Uvicorn auto-reload (dev mode)."
    )

    return parser.parse_args()

# ======================================
# 4. Main Logic
# ======================================
def main():
    args = parse_args()

    if args.command == "scrape":
        logger.info("Starting the CSR scraper pipeline...")
        if run_scraper:
            run_scraper(max_companies=args.max_companies)
        else:
            logger.error("Scraper module not found or not imported.")
        logger.info("Finished the CSR scraping process!")

    elif args.command == "analysis":
        logger.info("Starting analysis pipeline...")
        if run_analysis:
            run_analysis(quick_mode=args.quick)
        else:
            logger.error("Analysis pipeline not found or not imported.")
        logger.info("Finished the analysis pipeline!")

    elif args.command == "fix":
        logger.info("Running fix/cleanup script...")
        if run_fix_and_cleanup:
            run_fix_and_cleanup(dry_run=args.dry_run)
        else:
            logger.error("Fix/cleanup script not found or not imported.")
        logger.info("Cleanup tasks completed!")

    elif args.command == "index":
        logger.info("Creating/Updating MongoDB indexes...")
        if setup_indexes:
            setup_indexes()
        else:
            logger.error("Mongo index setup not found or not imported.")
        logger.info("Mongo indexes updated successfully!")

    elif args.command == "api":
        logger.info("Launching FastAPI server...")
        if fastapi_app:
            uvicorn.run(
                "modules.api.fastapi_api:app",
                host=args.host,
                port=args.port,
                reload=args.reload
            )
        else:
            logger.error("FastAPI app not found or not imported.")
        logger.info("FastAPI server stopped.")

# ======================================
# 5. Entry Point
# ======================================
if __name__ == "__main__":
    main()

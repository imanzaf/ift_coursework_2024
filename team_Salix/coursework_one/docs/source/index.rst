.. bigdata-Salix documentation master file, created by
   sphinx-quickstart on Wed Feb 26 00:17:50 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CSR Report Collection System's documentation!
================================================

This documentation covers the CSR Report Collection and Storage System, which automates the collection, processing, and storage of Corporate Social Responsibility (CSR) reports.

.. warning::
   **IMPORTANT NOTICE**

   * The ``docker-compose.yml`` file in the root directory contains incorrect Iceberg network configurations and should not be used.
   * We have provided a corrected version of the Docker Compose file inside the ``team_Salix`` directory.
   * Please follow the installation instructions exactly as written - do NOT move any configuration files out of the ``team_Salix`` directory.
   * All commands should be executed from within the ``team_Salix`` directory as specified in the installation guide below.

   **Make sure to use our updated versions of these files for proper system functionality.**

   Additionally:
   
   * The project structure must remain intact - do not move files between directories
   * All commands must be executed from within the ``team_Salix`` directory
   * Use the correct versions of SQL files:
     * ``create_db.sql``
     * ``create_tables.sql``
   * Follow the staged execution approach described in the installation guide

Project Structure
----------------

.. code-block:: text

   team_Salix/coursework_one/
   ├── a_pipeline/                  # Pipeline A: URL Crawling System
   │   ├── aresult/                # Storage for crawler results
   │   │   ├── cleaned_url.csv     # Processed and validated URLs
   │   │   └── crawler_logs/       # Crawler execution logs
   │   └── modules/
   │       ├── main.py            # Main URL crawler implementation
   │       └── notfoundclean.py   # URL validation and cleaning
   │
   ├── b_pipeline/                  # Pipeline B: PDF Processing System
   │   ├── bresult/                # Storage for PDF processing results
   │   │   ├── csr_reports/       # Downloaded CSR reports
   │   │   ├── download_failed.txt # Failed download records
   │   │   └── pdf_check_report.csv # PDF validation results
   │   └── modules/
   │       ├── main.py            # PDF downloader implementation
   │       ├── check_pdf.py       # PDF validation and verification
   │       └── remove_damaged.py   # Cleanup for corrupted files

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   installation
   usage
   testing
   architecture

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api
   modules/index

Features
--------

* Automated CSR report discovery and download
* Intelligent URL validation and filtering
* PDF integrity checking and validation
* Structured storage with version control
* Comprehensive logging and error handling
* Weekly automated updates
* Docker containerization support

License
-------

This project is licensed under the MIT License. See the LICENSE file for details.

Indices and Tables
----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

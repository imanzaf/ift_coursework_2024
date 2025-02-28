Architecture Overview
====================

The CSR Report Crawler and Storage System is designed with a modular architecture consisting of two main pipelines and several supporting components.

System Components
----------------

Pipeline A: URL Crawler
~~~~~~~~~~~~~~~~~~~~~

The URL crawling pipeline is responsible for discovering CSR report URLs:

* Extracts company names from SQLite database
* Implements multiple search strategies
* Supports various report types (sustainability, ESG, CSR)
* Performs URL validation and filtering
* Outputs cleaned URLs to CSV format

Pipeline B: PDF Handler
~~~~~~~~~~~~~~~~~~~~~

The PDF processing pipeline manages report downloads and validation:

* Asynchronous PDF downloading with progress tracking
* PDF validation and integrity checking
* Automatic removal of damaged files
* Organized storage structure
* Detailed download statistics

Storage System
~~~~~~~~~~~~~

The storage system utilizes multiple components:

* MinIO object storage for report files
* PostgreSQL database for metadata
* Structured storage hierarchy
* Version control support

Project Structure
---------------

.. code-block:: text

   team_Salix/coursework_one/
   ├── a_pipeline/           # URL crawling pipeline
   │   └── modules/
   │       ├── main.py      # URL crawler
   │       └── notfoundclean.py  # URL cleaner
   ├── b_pipeline/           # PDF download pipeline
   │   └── modules/
   │       ├── main.py      # PDF downloader
   │       ├── check_pdf.py    # PDF validator
   │       └── remove_damaged.py  # Damaged file cleaner
   ├── docs/                # Sphinx documentation
   │   ├── build/          # Generated documentation
   │   └── source/         # Documentation source files
   ├── scheduler.py          # Automated task scheduler
   └── upload_to_minio.py    # MinIO storage uploader

Key Features
-----------

Automation
~~~~~~~~~

* Weekly scheduled execution
* Automated error recovery
* Progress tracking
* Comprehensive logging

Data Management
~~~~~~~~~~~~~~

* Structured storage hierarchy
* Version control
* Metadata management
* Data integrity validation

Error Handling
~~~~~~~~~~~~~

* Automatic retries
* Transaction management
* Error logging
* Data validation

Technology Stack
--------------

Core Technologies
~~~~~~~~~~~~~~~

* Python 3.13+
* Docker
* PostgreSQL
* MinIO

Key Libraries
~~~~~~~~~~~~

* pandas
* selenium
* boto3
* aiohttp
* PyPDF2
* psycopg2
* APScheduler 
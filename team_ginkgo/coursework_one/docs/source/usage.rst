Usage Guide
===========

This section explains how to use the CSR Report Data Processing System.

## Prerequisites
Before running the system, ensure you have installed all dependencies:

.. code-block:: bash

   poetry install

To activate the virtual environment, use:

.. code-block:: bash

   poetry shell

## Running the System
You can execute the full pipeline using the main controller:

.. code-block:: bash

   poetry run python modules/main.py

This will:
1. Initialize the database.
2. Scrape CSR report URLs.
3. Download reports and store them in MinIO.
4. Update database records.

## Running Modules Individually
You can also run each module separately:

### 1️⃣ Initialize Database
To create tables and populate the database:

.. code-block:: bash

   poetry run python modules/database.py

### 2️⃣ Scrape CSR Reports
To search for and store CSR report URLs:

.. code-block:: bash

   poetry run python modules/scraper.py

### 3️⃣ Download and Store Reports
To fetch PDFs and upload them to MinIO:

.. code-block:: bash

   poetry run python modules/minio_client.py

### 4️⃣ Schedule Automated Tasks
To enable automatic execution every quarter:

.. code-block:: bash

   poetry run python modules/scheduler.py

## Checking the Database
To manually inspect stored CSR reports:

.. code-block:: sql

   SELECT * FROM Ginkgo.csr_reports;

This will display all stored CSR report records.

## Troubleshooting
If you encounter issues, try the following:

- Ensure dependencies are installed:  
  .. code-block:: bash

     poetry install

- Verify MinIO and PostgreSQL services are running.
- Check logs for errors.

For more details, refer to the API documentation.

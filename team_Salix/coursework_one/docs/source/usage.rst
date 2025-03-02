Usage Instructions
=================

This guide explains how to use the CSR Report Crawler and Storage System.

Running the Pipeline
------------------

.. warning::
   DO NOT run all scripts at once! The first script takes 5+ hours to fully complete.

Step 1: Initial Data Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the URL crawler for 10-15 minutes:

.. code-block:: bash

   poetry run python a_pipeline/modules/main.py

.. note::
   Let this run for at least 10-15 minutes, then manually stop it using CTRL + C.
   This ensures sufficient data processing for subsequent scripts.

Step 2: Process URLs and Download Reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the following scripts in order:

.. code-block:: bash

   poetry run python a_pipeline/modules/notfoundclean.py
   poetry run python b_pipeline/modules/main.py
   poetry run python b_pipeline/modules/check_pdf.py
   poetry run python b_pipeline/modules/remove_damaged.py

.. important::
   Run each script one at a time and wait for completion before starting the next.

Step 3: Upload to Storage
~~~~~~~~~~~~~~~~~~~~~~

Upload processed reports to MinIO:

.. code-block:: bash

   poetry run python upload_to_minio.py

Automated Scheduling
------------------

To enable weekly automated updates:

.. code-block:: bash

   poetry run python scheduler.py

This will schedule the pipeline to run every Monday at 3:00 AM.

Monitoring and Logs
-----------------

The system maintains several log files:

* Crawler logs: ``a_pipeline/aresult/crawler_log_[timestamp].txt``
* Download logs: ``b_pipeline/bresult/download_failed.txt``
* PDF validation report: ``b_pipeline/bresult/pdf_check_report.csv``

Storage Structure
---------------

The system organizes downloaded reports in a structured hierarchy:

* Reports are stored by company name
* Each company folder contains year-based subfolders
* Multiple versions of reports are supported
* Metadata is stored in PostgreSQL database

Error Handling
-------------

The system includes robust error handling:

* Automatic retry for failed downloads
* Damaged PDF detection and removal
* Comprehensive error logging
* Transaction rollback support 
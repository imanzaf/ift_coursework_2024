Installation Guide
==================

.. warning::
   **IMPORTANT NOTICE**

   * The ``docker-compose.yml`` file in the root directory contains incorrect Iceberg network configurations and should not be used.
   * We have provided a corrected version of the Docker Compose file inside the ``team_Salix`` directory.
   * Please follow the installation instructions exactly as written - do NOT move any configuration files out of the ``team_Salix`` directory.
   * All commands should be executed from within the ``team_Salix`` directory as specified in this guide.

This guide will help you set up and run the CSR Report Crawler and Storage System.

Prerequisites
------------

* Python 3.13+
* Docker
* Poetry

Step-by-Step Installation
------------------------

Step 1: Navigate to Project Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before running any commands, open a terminal and navigate to the *team_Salix* directory:

.. code-block:: bash

   cd path/to/team_Salix

Step 2: Clean Up Docker Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before starting fresh, remove all previous Docker containers, networks, and images:

.. code-block:: bash

   docker stop $(docker ps -aq) 2>/dev/null
   docker rm $(docker ps -aq) 2>/dev/null
   docker network prune -f
   docker volume prune -f
   docker system prune -a -f

Step 3: Verify Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure Docker and Poetry are installed:

.. code-block:: bash

   docker --version
   poetry --version

Step 4: Start Docker Services
~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Docker is verified, start all required services:

.. code-block:: bash

   docker compose up --build -d

Step 5: Install Python Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Docker is running, install all required Python dependencies:

.. code-block:: bash

   cd coursework_one
   rm -rf .venv
   poetry env remove --all
   poetry install --no-root

Step 6: Execute the Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::
   **DO NOT run all scripts at once!**
   The first script takes 5+ hours to fully complete. Instead, follow this staged approach:

1️⃣ Run Initial Data Extraction (Wait 10-15 minutes):

   .. code-block:: bash

      poetry run python a_pipeline/modules/main.py

   Let this run for at least 15-20 minutes, then manually stop it by pressing CTRL + C.
   
   .. note::
      Running for at least 15-20 minutes ensures that data processing starts and allows later scripts to execute correctly.

2️⃣ Continue with the Remaining Scripts (One by One):

   .. code-block:: bash

      poetry run python a_pipeline/modules/notfoundclean.py
      poetry run python b_pipeline/modules/main.py
      poetry run python b_pipeline/modules/check_pdf.py
      poetry run python b_pipeline/modules/remove_damaged.py

   .. warning::
      Run each script one at a time and let it fully complete before running the next!

3️⃣ Upload Processed Data to MinIO:

   .. code-block:: bash

      poetry run python upload_to_minio.py

Step 7: Generate and View Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After running the pipeline, you can generate and view the detailed API documentation:

.. code-block:: bash

   # Generate documentation
   cd docs
   poetry run make html

   # View in browser (choose based on your OS)
   open build/html/index.html  # On macOS
   # or
   xdg-open build/html/index.html  # On Linux
   # or manually open in your browser

The documentation includes:
   * Complete API reference
   * Module descriptions
   * Usage examples
   * Search functionality

Step 8: Enable Automatic Updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable weekly automated updates:

.. code-block:: bash

   cd ..  # Return to coursework_one directory if you're in docs
   poetry run python scheduler.py

Environment Configuration
-----------------------

The system requires the following environment variables:

* ``MINIO_ENDPOINT``: MinIO server endpoint (default: http://localhost:9000)
* ``MINIO_ACCESS_KEY``: MinIO access key
* ``MINIO_SECRET_KEY``: MinIO secret key
* ``POSTGRES_HOST``: PostgreSQL host
* ``POSTGRES_PORT``: PostgreSQL port
* ``POSTGRES_DB``: Database name
* ``POSTGRES_USER``: Database user
* ``POSTGRES_PASSWORD``: Database password

Dependencies
-----------

Key Python packages required:

* pandas >= 2.2.3
* selenium >= 4.29.0
* boto3 >= 1.36.26
* aiohttp >= 3.11.13
* PyPDF2 >= 3.0.1
* psycopg2-binary >= 2.9.10
* APScheduler >= 3.10.1 
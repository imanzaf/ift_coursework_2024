Installation Guide
==================

This guide provides step-by-step instructions on how to set up and run the CSR Report Data Processing System.

## Prerequisites
Before proceeding, ensure you have installed:
- **Python 3.9+**
- **Docker & Docker Compose**
- **Poetry** (for package management)
- **Git**

## Step 1: Clone the Repository
Clone the project from GitHub:
.. code-block:: bash

    git clone https://github.com/iftucl/ift_coursework_2024.git
    cd ift_coursework_2024/team_Ginkgo

## Step 2: Install Dependencies
Use Poetry to install all required dependencies:
.. code-block:: bash

    poetry install

## Step 3: Set Up the Database
Ensure PostgreSQL is running, then create the required database schema and tables:
.. code-block:: bash

    poetry run python database.py

## Step 4: Configure Environment Variables
Modify `config.py` to set up your:
- **Google API Key**
- **Database Credentials**
- **MinIO Credentials**

## Step 5: Start the System
Run the following command to start all services:
.. code-block:: bash

    docker-compose up --build -d

## Step 6: Verify Installation
To check if everything is set up correctly, run:
.. code-block:: bash

    poetry run python main.py

Database Module
===============

This module contains functions to interact with the PostgreSQL database. It ensures that the `Ginkgo` schema
and the `csr_reports` table exist and inserts company data for the years 2014 to 2023.

.. automodule:: database
   :members:
   :undoc-members:
   :show-inheritance:

Function Details
----------------

insert_companies
^^^^^^^^^^^^^^^^

.. autofunction:: database.insert_companies

This function performs the following tasks:

1. Connects to the PostgreSQL database using the configuration provided in `DB_CONFIG`.
2. Ensures the `Ginkgo` schema and the `csr_reports` table exist.
3. Fetches all companies from the `csr_reporting.company_static` table.
4. Inserts company data for each company and each year from 2014 to 2023.
5. Uses `ON CONFLICT DO NOTHING` to avoid duplicate entries.

**Console Output:**
- ✅ Database setup completed!
- Successfully inserted companies into csr_reports

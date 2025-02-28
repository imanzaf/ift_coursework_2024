Data Models Package
===================

This package contains the data models used in the project. These models define the structure of the data
and provide validation using Pydantic. The models are designed to represent entities such as companies,
ESG reports, and other related data.

.. rubric:: **Key Features**

- Define the structure of data using Pydantic models.
- Validate data inputs to ensure consistency and correctness.
- Support for nested models and relationships between entities.

Data Models Module
-------------------

.. automodule:: src.data_models.company
   :members:
   :show-inheritance:
   :undoc-members:
   :exclude-members: model_config, country, esg_reports, gics_industry, gics_sector, region, security, symbol, url, year, author, link, metatag_title, snippet, title

   .. rubric:: **Overview**

   The `company` module contains the `Company` and `ESGReport` classes, which represent companies and their
   associated ESG (Environmental, Social, and Governance) reports. These models are used to validate and
   structure data related to companies and their ESG activities.

   .. rubric:: **Key Features**

   - **Company Class**: Represents a company with attributes such as stock symbol, name, sector, industry,
     location, and associated ESG reports.
   - **ESGReport Class**: Represents an ESG report with attributes such as URL and publication year.
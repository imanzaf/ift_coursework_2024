ESG Reports Package
===================

.. rubric:: **Overview**

This package contains modules for handling ESG (Environmental, Social, and Governance) reports. It includes functionality for searching and validating ESG reports, ensuring data accuracy and consistency.

.. rubric:: **Key Features**

- Search for ESG reports using various criteria.
- Validate ESG reports to ensure compliance with required standards.
- Integrate with external APIs and databases for data retrieval and validation.

ESG Reports Search Module
-------------------------

.. automodule:: src.esg_reports.search
   :members:
   :show-inheritance:
   :undoc-members:
   :exclude-members: company, model_config

   .. rubric:: **Overview**

   The `search` module provides functionality for searching ESG reports. It includes methods for querying external APIs or databases to retrieve ESG reports based on specific criteria such as company name, report year, or keywords.

   .. rubric:: **Key Features**

   - Query ESG reports using flexible search parameters.
   - Integrate with external APIs for real-time data retrieval.
   - Filter and sort search results for better usability.

ESG Reports Validate Module
---------------------------

.. automodule:: src.esg_reports.validate
   :members:
   :show-inheritance:
   :undoc-members:
   :exclude-members: company, model_config

   .. rubric:: **Overview**

   The `validate` module provides functionality for validating ESG reports. It ensures that ESG reports meet required standards and formats, and it performs checks for data completeness and accuracy.

   .. rubric:: **Key Features**

   - Validate ESG report data against predefined standards.
   - Check for missing or inconsistent data.
   - Generate validation reports for further analysis.
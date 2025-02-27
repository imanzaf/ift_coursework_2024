config
=============

.. rubric:: **Overview**

This section provides an overview of the configuration modules in the project. These modules handle settings and configurations for various components, such as database connections and search functionality.

.. rubric:: **Key Features**

- **Database Settings**: Manages database connection settings and configurations.
- **Search Settings**: Handles configurations for search-related functionality.

Database Settings Module
------------------------

.. automodule:: config.db
   :members:
   :show-inheritance:
   :undoc-members:
   :exclude-members: MINIO_BUCKET_NAME, MINIO_HOST, MINIO_PASSWORD, MINIO_PORT, MINIO_USERNAME, POSTGRES_DB_NAME, POSTGRES_DRIVER, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USERNAME, model_config

Search Settings Module
----------------------

.. automodule:: config.search
   :members:
   :show-inheritance:
   :undoc-members:
   :exclude-members: GOOGLE_API_KEY, GOOGLE_API_URL, GOOGLE_ENGINE_ID, SUSTAINABILITY_REPORTS_API_URL, model_config
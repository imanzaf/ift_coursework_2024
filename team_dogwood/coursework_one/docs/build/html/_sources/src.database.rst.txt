Database Package
================

This package contains modules for interacting with databases and storage services, including **PostgreSQL** for relational data and **MinIO** for object storage.

Database Minio Module
---------------------

.. automodule:: src.database.minio
   :members:
   :show-inheritance:
   :undoc-members:
   :exclude-members: bucket_name, endpoint_url, model_config, password, user, 

   .. rubric:: **Overview**

   The `minio` module provides functionality for interacting with **MinIO**, an open-source object storage service. It includes methods for uploading, downloading, and managing files stored in MinIO buckets.

   .. rubric:: **Key Features**

   - Upload files to MinIO buckets.
   - Download files from MinIO buckets.
   - Manage bucket policies and configurations.

Database Postgres Module
------------------------

.. automodule:: src.database.postgres
   :members:
   :show-inheritance:
   :undoc-members:
   :exclude-members: model_config

   .. rubric:: **Overview**

   The `postgres` module provides functionality for interacting with **PostgreSQL**, a powerful open-source relational database. It includes methods for querying, inserting, updating, and deleting data in PostgreSQL tables.

   .. rubric:: **Key Features**

   - Execute SQL queries.
   - Insert, update, and delete records.
   - Manage database connections and transactions.
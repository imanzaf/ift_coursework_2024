'''
This file contains the configuration for the project.
The main configuration settings include:
- Google API Key
- Google Custom Search Engine ID
- Database Configuration
- MINIO Configuration
These settings are used by the different modules of the project to interact with external services and resources.
For example, the Google API Key is used to access Google Custom Search API, the Database Configuration is used to connect to the SQL database, and the MINIO Configuration is used to store and retrieve files from the MINIO object storage service.

'''
# Google API Key
GOOGLE_API_KEY = "AIzaSyCgYeXx0D-kHYOyCz1q0xsVwWq-g5lNLtg"

# Google Custom Search Engine ID
GOOGLE_CX = "b5e302fa89034451f"

# Database Configuration
DB_CONFIG = {
    "dbname": "fift",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5439
}

# MINIO Configuration
MINIO_CONFIG = {
    "endpoint": "localhost:9000",
    "access_key": "ift_bigdata",
    "secret_key": "minio_password",
    "bucket": "csreport"
}


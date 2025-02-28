Usage Instructions
====================

Configuration
--------------
Before running the project, make sure you have PostgreSQL, MongoDB, and MinIO running. Edit the configuration file `config.yaml` to include your MinIO credentials and PostgreSQL connection details.

minio:
  endpoint: "localhost:9000"
  MINIO_ROOT_USER=ift_bigdata
  MINIO_ROOT_PASSWORD=minio_password
  MINIO_DOMAIN=miniocw
  secure: false

postgres:
  host: "localhost"
  port: 5439
  user: "postgres"
  password: "postgres"
  database: "ift_bigdata"

mongo_db:
   ME_CONFIG_BASICAUTH_USERNAME=mongodb_express
   ME_CONFIG_BASICAUTH_PASSWORD=mongodb_express
   ME_CONFIG_MONGODB_SERVER=mongo_db
   ME_CONFIG_MONGODB_PORT=27017


Quick Start Guide
----------------------------
1. Clone the repository:
   ```bash
   git clone https://github.com/JJJJJJoseph/ift_coursework_2024.git
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the scraper:
   ```bash
   python run_scraper.py
   ```

The script will automatically fetch CSR reports and store them in MinIO.

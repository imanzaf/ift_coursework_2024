Installation Guide
======================

This project provides a set of utilities for scraping CSR reports from various online sources, storing them in a cloud storage (MinIO), and indexing them in a MongoDB database.

System Requirements
-----------------------
- **Operating System**: Windows 10 or Linux (Ubuntu 20.04+)
- **Python**: Python 3.7 or higher
- **Disk Space**: At least 1GB of free space for installation
- **Memory**: 4GB RAM or more

Installation Dependencies
------------------------------
Before you can run this project, you need to install the following dependencies:

1. **Python 3.7+**
2. **PostgreSQL** - for database access.
3. **MinIO** - for cloud object storage.
4. **MongoDB** - for report information storage.
5. **Required Python libraries**:
   - `requests`
   - `selenium`
   - `psycopg2`
   - `pymongo`
   - `minio`
   - `chromedriver_autoinstaller`

To install the Python dependencies, you can use the following:

```bash
pip install -r requirements.txt
```

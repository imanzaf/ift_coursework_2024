API reference for fix and cleanup
=========================================

This script is designed to fix and clean up CSR (Corporate Social Responsibility) report data stored in MongoDB and MinIO. It performs three main tasks:
1. **Fix CSR report year** by extracting the year from the corresponding PDF files.
2. **Fix ingestion_time** by converting it into a string format.
3. **Remove duplicate PDF files** based on company name and report year.

Base URL
---------
- **MongoDB URI**: `mongodb://localhost:27019`
- **MinIO Host**: `localhost:9000`
- **MinIO Bucket**: `csr-reports`

Overview
--------
This script processes CSR reports by interacting with MongoDB and MinIO:
1. Downloads the CSR PDF files from MinIO.
2. Extracts and corrects the CSR report year based on the content of the PDF files.
3. Ensures the `ingestion_time` field in MongoDB is formatted as an ISO string.
4. Deletes duplicate PDF files from MinIO based on the same company and report year, keeping only the first occurrence.

Tasks
-----
### Task 1: Fix CSR Report Year
#### Function: `update_csr_year()`
This function downloads the CSR report PDFs from MinIO, extracts the year from the first two pages of the PDF, and updates the `csr_report_year` in MongoDB accordingly.

**Steps**:
1. Download the PDF file from MinIO.
2. Extract the year from the first two pages of the PDF.
3. Update the `csr_report_year` field in MongoDB with the extracted year.

**Logs**:
- Success: `"✅ Updated {company_name} year to {actual_year}"`
- Failure: `"⚠️ Failed to parse year for {company_name}"`

### Task 2: Fix Ingestion Time
#### Function: `fix_ingestion_time()`
This function ensures that the `ingestion_time` field in MongoDB is stored as a string in ISO format.

**Steps**:
1. Retrieve each document from MongoDB.
2. If `ingestion_time` is a `datetime` object, convert it to ISO format and update MongoDB.

**Logs**:
- Success: `"✅ Fixed {company_name}'s ingestion_time to ISO string format"`

### Task 3: Delete Duplicate PDFs
#### Function: `delete_duplicate_pdfs()`
This function identifies and removes duplicate PDF files based on the same company name and CSR report year. Only the first occurrence of a duplicate is kept, and the others are deleted from MinIO and MongoDB.

**Steps**:
1. Retrieve all CSR reports from MongoDB.
2. Check for duplicates based on `company_name` and `csr_report_year`.
3. Remove the duplicate PDF from MinIO and delete the corresponding document from MongoDB.

**Logs**:
- Success: `"✅ Removed duplicate {company_name}({csr_report_year})"`
- Failure: `"⚠️ Failed to delete {file_path}"`

How to Use
-----------
### Prerequisites:
1. **MongoDB**: Ensure MongoDB is running and accessible at the configured URI (`mongodb://localhost:27019`).
2. **MinIO**: Ensure MinIO is running with the correct bucket (`csr-reports`) configured.
3. **Dependencies**: Install the required Python packages:
```bash
pip install pymongo minio pdfplumber python-magic
```
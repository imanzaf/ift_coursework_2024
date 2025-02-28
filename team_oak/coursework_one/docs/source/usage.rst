Usage Instructions
==================

To use the CSR Report Storage system:

1. Run the scraper:
   .. code-block:: bash

      python main.py

2. View stored reports in MinIO:
   - Access the MinIO console at `http://localhost:9001`.
   - Use the bucket `csr report` to view uploaded reports.

3. Query metadata in PostgreSQL:
   .. code-block:: sql

      SELECT * FROM pdf_records WHERE company = 'TestCorp';
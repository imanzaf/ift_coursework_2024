API Reference for Analysis Pipeline
========================================

This document provides an overview of the functions and modules in the `analysis_pipeline.py` script.

Modules
-------
- **os**: Provides a portable way of using operating system dependent functionality.
- **io**: Provides Python’s main facilities for dealing with various types of I/O.
- **pymongo**: A Python driver for MongoDB, used for interacting with the MongoDB database.
- **minio**: MinIO Python Client SDK, used to interact with MinIO object storage.
- **pdfplumber**: A Python library used to extract text and data from PDF documents.
- **nltk**: The Natural Language Toolkit (NLTK), used for text processing and sentiment analysis.
- **yake**: A keyword extraction library used for extracting keywords from text.

Functions
---------

### extract_text_from_pdf(pdf_bytes)
```python
def extract_text_from_pdf(pdf_bytes: bytes) -> str
```

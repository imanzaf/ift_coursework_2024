Structure design Overview
==========================

This document provides an overview of the system architecture, challenges, and solutions for the CSR report management platform. The system facilitates the collection, processing, storage, and retrieval of Corporate Social Responsibility (CSR) reports for use by various stakeholders including investors, consumers, and regulatory bodies.

Project Overview
----------------

### Background

Corporate Social Responsibility (CSR) reports are essential disclosures made by companies about their environmental, social, and governance (ESG) practices. These reports provide stakeholders with insights into a company’s non-financial performance and are increasingly used by investors and consumers to make informed decisions.

The CSR report management system is designed to automate the retrieval, processing, and storage of these reports, facilitating easy access for stakeholders.

### Project Objectives

The goal of this project is to build a comprehensive system capable of:

- Automatically retrieving CSR reports from various company websites.
- Storing and organizing reports for easy retrieval.
- Providing stakeholders with a user-friendly interface to query and access reports.
  
System Architecture
-----------------------

The system is composed of several core components that work together to ensure the seamless extraction, processing, storage, and retrieval of CSR reports. These components are organized into the following layers:

### 1. Data Ingestion Layer
The data ingestion process involves the automated scraping of CSR reports from company websites using a web scraping tool. The system uses both `Requests + BeautifulSoup` for static content and `Selenium WebDriver` for dynamically rendered content.

### 2. Data Processing Layer
Once the reports are ingested, they undergo a series of transformations, including:

- Text extraction from PDFs using `PyMuPDF` for machine-readable PDFs and `Tesseract OCR` for scanned documents.
- Metadata extraction, including company name, reporting year, and sustainability theme.

### 3. Data Storage Layer
The data storage system is designed to store both structured and unstructured data. The key components include:

- **PostgreSQL**: Used for structured metadata such as company names, report years, and other attributes.
- **MongoDB**: Used for storing full-text metadata and additional unstructured data related to CSR reports.
- **MinIO**: Provides scalable storage for large CSR report PDFs.

### 4. Data Retrieval Layer
The system offers an API interface for querying CSR reports. The API enables users to search reports by company name, year, and other metadata. Additionally, the reports can be retrieved through a user-friendly web interface.

Challenges and Solutions
------------------------

### Web Scraping Challenges
One of the key challenges in the project was efficiently retrieving CSR reports from company websites, as they are published in various formats. The system employs a hybrid approach to handle both static and dynamic content.

### Data Storage Challenges
Storing unstructured CSR report files (typically PDFs) presents challenges in traditional relational databases. The solution integrates MinIO for scalable file storage while using PostgreSQL for structured metadata and MongoDB for report-related metadata.

### Data Quality Validation
Ensuring data integrity was a critical focus. The system employs robust validation rules to check for issues such as duplicate reports, incorrect metadata, and corrupt files. Outlier years and missing metadata are also corrected during the data processing stages.

System Implementation
---------------------

### Data Extraction

Data extraction is performed using a combination of web scraping technologies:

- **Selenium WebDriver**: Used for scraping dynamic pages.
- **Requests + BeautifulSoup**: Used for static page scraping.

Once the reports are located, they are downloaded and processed for storage.

### Data Validation

Validation is applied at various stages to ensure that the data is accurate and complete:

- **Duplicate detection**: Reports with identical metadata are detected and removed.
- **Outlier year correction**: Reports labeled with years outside of a reasonable range are adjusted.
- **Metadata completeness**: Missing metadata fields, such as company name or report URL, are flagged and handled.

### Data Storage

CSR reports are stored using a hybrid storage approach:

- **MinIO**: Stores the raw PDFs in an efficient object storage system.
- **PostgreSQL**: Stores structured company metadata.
- **MongoDB**: Stores unstructured metadata associated with CSR reports.

### Data Retrieval

The system provides an API and web interface for querying CSR reports. The API is designed to handle queries based on various metadata fields such as company name, reporting year, and sustainability themes.

### Security Considerations

Security measures are implemented to protect sensitive company data and ensure system integrity:

- Authentication and access control are enforced through JWT-based tokens.
- Data integrity is checked using checksum verification and file header checks.

Testing and Optimization
------------------------

### Testing Strategy

The testing framework ensures that each part of the pipeline functions correctly. Tests are divided into:

- **Unit tests**: Validate the smallest functional units of the code.
- **Integration tests**: Ensure multiple components work together correctly.
- **API tests**: Ensure that API endpoints respond with the correct data.

### Performance Optimization

Several techniques were implemented to optimize system performance:

- **MongoDB indexing**: Indexes on company name and report year ensure fast queries.
- **Concurrency in web scraping**: The use of multi-threading reduces the time taken for large-scale crawls.

Future Improvements
-------------------

While the system is fully functional, there are several areas for future enhancements:

- **Expanded data sources**: Integrate additional sources like APIs and government databases for more CSR reports.
- **AI-driven analysis**: Implement natural language processing (NLP) to extract deeper insights from CSR reports.
- **Real-time analytics**: Integrate real-time analytics for tracking trends in corporate sustainability.

Conclusion
==========

The CSR report management system provides an efficient and scalable solution for extracting, processing, storing, and retrieving corporate sustainability data. The system’s architecture is designed to be flexible, ensuring it can accommodate future expansions and improvements.


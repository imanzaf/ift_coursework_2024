"""
PDF Validation Module

This module provides functionality to validate PDF files by checking their integrity,
readability, and basic structure. It includes functions to scan directories of PDFs
and generate detailed reports about their status.
"""

import os
import PyPDF2
from tqdm import tqdm
import pandas as pd
from PyPDF2.errors import PdfReadError  # Import error class correctly

def check_pdf(file_path):
    """
    Check if a PDF file can be opened and read normally.
    
    This function performs several checks on a PDF file:
    1. Verifies file size is not zero
    2. Validates PDF header
    3. Checks if file is encrypted
    4. Attempts to read pages and extract text
    
    Args:
        file_path (str): Path to the PDF file to check
        
    Returns:
        tuple: (bool, str/int) where:
            - bool: True if file is valid, False otherwise
            - str/int: Number of pages if valid, error message if invalid
    """
    try:
        # First check file size
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        if file_size == 0:
            return False, "File size is 0"
            
        with open(file_path, 'rb') as file:
            # Check if file header is PDF format
            header = file.read(4)
            if header != b'%PDF':
                return False, "Not a valid PDF file format"
            
            file.seek(0)  # Reset file pointer to start
            try:
                # Try to read PDF
                reader = PyPDF2.PdfReader(file)
                
                # Check if encrypted
                if reader.is_encrypted:
                    try:
                        # Try to decrypt with empty password
                        reader.decrypt('')
                    except:
                        return False, "PDF file is encrypted and cannot be decrypted"
                
                # Check page count
                try:
                    num_pages = len(reader.pages)
                    if num_pages == 0:
                        return False, "PDF file has 0 pages"
                    
                    # Try to read first page
                    first_page = reader.pages[0]
                    first_page.extract_text()  # Try to extract text
                    return True, num_pages
                except Exception as e:
                    return False, f"Cannot read pages: {str(e)}"
                    
            except PyPDF2.errors.DependencyError:
                return False, "PyCryptodome library required to handle encrypted PDFs"
            except Exception as e:
                return False, f"PDF reading error: {str(e)}"
                
    except Exception as e:
        return False, str(e)

def scan_directory(root_dir):
    """
    Scan all PDF files in a directory and check their validity.
    
    This function recursively traverses a directory structure, identifies PDF files,
    and validates each one. It maintains progress information and generates detailed
    reports about the status of each file.
    
    Args:
        root_dir (str): Root directory to scan for PDF files
        
    Returns:
        tuple: (list, list) containing:
            - list: All results including both valid and invalid files
            - list: Only damaged files for further processing
    """
    results = []
    damaged_files = []
    
    # Traverse directory
    print("Starting to scan PDF files...")
    total_pdfs = sum([len(files) for _, _, files in os.walk(root_dir) if any(f.endswith('.pdf') for f in files)])
    
    with tqdm(total=total_pdfs, desc="Checking Progress") as pbar:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, root_dir)
                    
                    # Extract company name and year from filename
                    # Example: ./downloadpdfs/Apple/2020/Apple_2020.pdf
                    path_parts = relative_path.split(os.sep)
                    company = path_parts[0]  # First level directory is company name
                    year = path_parts[1]     # Second level directory is year
                    
                    # Check PDF
                    is_valid, info = check_pdf(file_path)
                    
                    result = {
                        'company': company,
                        'year': year,
                        'file_name': file,
                        'status': 'Valid' if is_valid else 'Damaged',
                        'pages': info if is_valid else 0,
                        'error': '' if is_valid else info,
                        'file_path': file_path,
                        'file_size': os.path.getsize(file_path) / (1024 * 1024)  # File size (MB)
                    }
                    
                    results.append(result)
                    if not is_valid:
                        damaged_files.append(result)
                    
                    pbar.update(1)

    return results, damaged_files

def main():
    """
    Main function to orchestrate PDF validation process.
    
    This function:
    1. Sets up the directory structure
    2. Initiates the PDF scanning process
    3. Generates and saves a detailed report
    4. Prints summary statistics
    
    The function creates a CSV report containing details about all scanned files,
    including their status, size, and any error messages for invalid files.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
    # Set PDF file root directory to b_pipeline/bresult/csr_reports
    b_pipeline_dir = os.path.dirname(os.path.dirname(__file__))  # Get b_pipeline directory
    root_dir = os.path.join(b_pipeline_dir, "bresult", "csr_reports")
    
    # Print paths for debugging
    print(f"Looking for PDFs in: {root_dir}")
    print(f"Current script directory: {script_dir}")
    print(f"B_pipeline directory: {b_pipeline_dir}")
    
    # Check if directory exists
    if not os.path.exists(root_dir):
        print(f"Creating directory: {root_dir}")
        os.makedirs(root_dir, exist_ok=True)
        return
    
    # Scan and check PDF files
    results, damaged_files = scan_directory(root_dir)
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Set report file storage in b_pipeline/bresult directory
    report_dir = os.path.join(b_pipeline_dir, "bresult")  # Use previously defined b_pipeline_dir
    os.makedirs(report_dir, exist_ok=True)  # Ensure directory exists
    report_file = os.path.join(report_dir, "pdf_check_report.csv")
    print(f"Report will be saved to: {report_file}")  # Print path for debugging
    df.to_csv(report_file, index=False, encoding='utf-8')
    
    # Print statistics
    total_files = len(results)
    damaged_count = len(damaged_files)
    print("\n📊 Check Statistics:")
    print(f"Total files: {total_files}")
    print(f"Valid files: {total_files - damaged_count}")
    print(f"Damaged files: {damaged_count}")
    
    # If there are damaged files, print detailed information
    if damaged_files:
        print("\n❌ Damaged PDF files:")
        for file in damaged_files:
            print(f"\nCompany: {file['company']}")
            print(f"Year: {file['year']}")
            print(f"File: {file['file_name']}")
            print(f"Error: {file['error']}")
    
    print(f"\nComplete report has been saved to: {report_file}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL Cleaning Module
==================

This module processes a CSV file containing URLs and removes entries marked as "Not found".
It is part of the data pipeline that handles sustainability report URLs.

The module performs the following operations:
    1. Reads a CSV file containing URLs from the results of the crawler
    2. Removes rows where the URL is marked as "Not found"
    3. Saves the cleaned data to a new CSV file

Module Attributes:
    BASE_DIR (str): The absolute path to the modules directory
    PIPELINE_DIR (str): The absolute path to the pipeline root directory
    
Dependencies:
    - pandas
    - os

Example:
    To use this module, simply run it as a script::

        $ python notfoundclean.py

    The script will automatically process the input file and generate a cleaned output file.

Author: Shijie Zhang
Created on: Fri Feb 21 10:05:41 2025
"""

import pandas as pd
import os

# Get current script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # modules directory
PIPELINE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # a_pipeline directory

# Print paths for debugging
print(f"BASE_DIR: {BASE_DIR}")
print(f"PIPELINE_DIR: {PIPELINE_DIR}")

def clean_urls(input_file: str, output_dir: str) -> str:
    """
    Clean the URLs dataset by removing entries marked as "Not found".

    This function processes a CSV file containing URLs from the web crawler results.
    It removes rows where the URL is marked as "Not found" and saves the cleaned
    dataset to a new CSV file. The function is designed to work with the output
    from the sustainability report crawler.

    Args:
        input_file (str): Path to the input CSV file containing URLs.
            The file should have a 'url' column containing the URLs or "Not found" markers.
            Example format:
            company,year,url,source
            Apple,2024,http://example.com/report.pdf,Bing
            Microsoft,2024,Not found,Not found

        output_dir (str): Directory where the cleaned file will be saved.
            The directory will be created if it doesn't exist.
            The output file will be named "cleaned_url.csv".

    Returns:
        str: Path to the cleaned output file.
            The output file will be saved as "{output_dir}/cleaned_url.csv".

    Raises:
        FileNotFoundError: If the input file doesn't exist or can't be accessed.
        PermissionError: If there are permission issues with reading/writing files.
        pd.errors.EmptyDataError: If the input file is empty.
        pd.errors.ParserError: If the input file is not a valid CSV.

    Note:
        - The function preserves all columns from the input file
        - Only rows with "Not found" in the URL column are removed
        - The output is saved without the pandas index
        - UTF-8 encoding is used for file operations
        - The original file is not modified

    Example:
        >>> input_file = "results_dirty_urls.csv"
        >>> output_dir = "cleaned_results"
        >>> cleaned_file = clean_urls(input_file, output_dir)
        >>> print(f"Cleaned file saved as: {cleaned_file}")
        Cleaned file saved as: cleaned_results/cleaned_url.csv
    """
    # Read input file
    df = pd.read_csv(input_file)

    # Ensure URL column exists
    url_column = "url" if "url" in df.columns else None

    # Remove rows containing "not found" in URL column
    if url_column:
        df_cleaned = df[df[url_column] != "Not found"]
    else:
        df_cleaned = df

    # Save cleaned data
    cleaned_file_path = os.path.join(output_dir, "cleaned_url.csv")
    df_cleaned.to_csv(cleaned_file_path, index=False)
    
    return cleaned_file_path

if __name__ == "__main__":
    # Ensure using correct path
    input_file = os.path.join(PIPELINE_DIR, "a_pipeline", "aresult", "results_dirty_urls.csv")
    print(f"Looking for file at: {input_file}")

    # Output directory (a_pipeline/aresult)
    output_dir = os.path.join(PIPELINE_DIR, "a_pipeline", "aresult")
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

    # Process the file
    cleaned_file_path = clean_urls(input_file, output_dir)
    print(f"Cleaned file has been saved as: {cleaned_file_path}")
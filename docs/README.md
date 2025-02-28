# Rename Guidelines for Coursework and Documentation Files

This document outlines the suggested naming conventions and file organization for the coursework repository related to the "Big Data in Quantitative Finance" module (2024-25). The guidelines are based on the content and structure of the repository.

## Project Structure Overview

The project consists of several folders and files crucial for different aspects of coursework. Below is an organized description of the files and suggested naming conventions for better clarity and structure.

### Directory Structure

1. **Main Repository Folder: `ift_coursework_2024`**
   - Contains all coursework-related materials, including team-specific files and configuration.
   
2. **Team Directories**
   - **`Magnolia/`**: Contains team Magnolia's coursework files.
   - Other team directories: The folders for the other teams should be clearly labeled with the team name (e.g., `team_sakura`, `team_acer`, etc.).

3. **Documentation Files**
   - **`README.md`**: Overview of the repository and coursework details.
   - **`requirements.txt`**: Lists the Python dependencies required for the project.
   - **`installation_guide.rst`**: Instructions on how to set up the project environment.
   - **`usage_instruction.rst`**: Provides usage instructions for the system or API.
   - **`structure_design.rst`**: Documents the system's design structure.
   - **`api_pipline.rst`**: Explains the API pipeline used in the project.
   - **`csr_api.rst`**: Details about the CSR API.
   - **`csr_fix_and_cleanup.rst`**: Instructions for fixing and cleaning up CSR data.
   - **`index.rst`**: The main index file for Sphinx documentation.
   
4. **Configuration Files**
   - **`conf.py`**: Configuration for Sphinx documentation builder.
     - **Project Information**: Defines the project name as `ift_bigdata_csr_reports`, with a release version of `0.0.1`.
     - **Extensions**: Includes any necessary Sphinx extensions for documentation generation.
     - **HTML Output**: Uses the `furo` theme for the generated HTML documentation.
   - **`.gitignore`**: Standard git ignore file to avoid committing unnecessary files.
   - **`.venv/`**: Directory for the Python virtual environment.
   - **`.git/`**: Git version control directory.

### File Renaming Recommendations

- **Team Files**: Ensure all team folders are consistently named using the format `team_<teamname>`. For example, `team_oak`, `team_sakura`, etc.
  
- **Documentation Files**: 
   - Ensure all documentation files use `.rst` for reStructuredText files and `.md` for markdown files.
   - Maintain consistent naming for similar files across the documentation (e.g., `usage_instruction.rst`, `installation_guide.rst`, etc.).
  
- **Configuration Files**:
   - Keep the configuration file `conf.py` as-is, as it is essential for Sphinx documentation.
   - Ensure the `requirements.txt` file lists all necessary dependencies, as found in the current file.

### Important Notes

- The use of **Sphinx** for generating HTML documentation is required, as indicated in `conf.py`.
- Ensure all dependencies in `requirements.txt` are installed with the command: 

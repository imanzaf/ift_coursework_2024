import os
import sys

# Get the current directory of conf.py
current_dir = os.path.abspath(os.path.dirname(__file__))

# Ensure Sphinx can find the Python code inside the "modules" directory
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
modules_path = os.path.join(project_root, "modules")

sys.path.insert(0, project_root)  # Add project root to sys.path
sys.path.insert(0, modules_path)  # Add "modules/" to sys.path

print(f"Added to sys.path: {modules_path}")  # Debug output

# -- Project information -----------------------------------------------------
project = 'CSR Data Pipeline'
copyright = '2025, Team Ginkgo'
author = 'Team Ginkgo'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',  # Parse docstrings
    'sphinx.ext.napoleon', # Support Google/NumPy docstring formats
    'sphinx.ext.viewcode', # Enable source code visualization
]

templates_path = ['_templates']
exclude_patterns = []
language = 'en'

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']

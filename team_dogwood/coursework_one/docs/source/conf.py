import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Team Dogwood"
copyright = "2025, Gabriella Larrisa"
author = "Gabriella Larrisa"
release = "1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]

templates_path = ["_templates"]
exclude_patterns = []

language = "en"

# Napoleon settings
napoleon_google_docstring = True  # Enable Google-style docstrings
napoleon_numpy_docstring = False  # Disable NumPy-style docstrings (optional)
napoleon_include_init_with_doc = True  # Include __init__ docstrings
napoleon_include_private_with_doc = True  # Include private methods
napoleon_include_special_with_doc = True  # Include special methods (e.g., __str__)
napoleon_use_admonition_for_examples = True  # Use admonitions for examples
napoleon_use_admonition_for_notes = True  # Use admonitions for notes
napoleon_use_admonition_for_references = True  # Use admonitions for references
napoleon_use_ivar = True  # Use "ivar" for instance variables
napoleon_use_param = True  # Use "param" for parameters
napoleon_use_rtype = True  # Use "rtype" for return types


autodoc_default_options = {
    "members": True,  # Document all members (methods, attributes, etc.)
    "undoc-members": False,  # Include members without docstrings
    "show-inheritance": False,  # Show class inheritance
    "private-members": False,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

extensions.append("sphinx_wagtail_theme")
html_theme = "sphinx_wagtail_theme"
html_theme_options = dict(
    project_name="Team Dogwood",
)
html_static_path = ["_static"]

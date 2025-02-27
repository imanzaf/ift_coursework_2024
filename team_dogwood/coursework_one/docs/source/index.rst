.. Team Dogwood documentation master file, created by
   sphinx-quickstart on Tue Feb 25 03:03:02 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Team Dogwood's Documentation!
========================================

This is the official documentation for **Team Dogwood's** project. Here, you'll find detailed information about the project's modules, configuration, and usage.

.. note::
   This documentation is written using ``reStructuredText`` (reST). For more details on reST syntax, refer to the
   `reStructuredText documentation <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_.

Installation Guide
-------------------

To get started with the project, follow these steps:

1. **Clone the Repository**: If you haven't already, clone the repository using Git.

   .. code-block:: bash

      git clone https://github.com/imanzaf/ift_coursework_2024.git

2. **Install Python and Poetry**:  
   - Ensure you have Python installed. You can download it from `python.org <https://www.python.org/downloads/>`_.
   - Install Poetry by following the `official Poetry installation guide <https://python-poetry.org/docs/#installation>`_.

3. **Navigate to the Project Directory**: Move into the cloned repository directory.

   .. code-block:: bash

      cd team_dogwood/coursework_one

4. **Install Dependencies**: Use Poetry to install the project dependencies.

   .. code-block:: bash

      poetry install

5. **Set Up Environment Variables**: Create a `.env` file in the root directory and populate it with the required environment variables.

6. **Run the Project**: Use Poetry to run the main script.

   .. code-block:: bash

      poetry run python main.py


Project Structure
-------------------

The project is organized into the following modules:

- **`config`**: Contains configuration settings for the project.
- **`src`**: Contains the main source code, including data models, database interactions, and utility functions.

For more details, refer to the :ref:`modules` section.

API Reference
--------------

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   modules
   config

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
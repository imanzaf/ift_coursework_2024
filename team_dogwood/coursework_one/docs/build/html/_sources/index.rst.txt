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

Getting Started
---------------

To get started with the project, follow these steps:

1. **Install Poetry**: If you don't have Poetry installed, follow the
   `official Poetry installation guide <https://python-poetry.org/docs/#installation>`_.

2. **Install Dependencies**: Use Poetry to install the project dependencies.

   .. code-block:: bash

      poetry install

3. **Set Up Environment Variables**: Create a `.env` file in the root directory and populate it with the required environment variables.

4. **Run the Project**: Use Poetry to run the main script.

   .. code-block:: bash

      poetry run python main.py

Project Structure
-------------------

The project is organized into the following modules:

- **`Config`**: Contains configuration settings for the project.
- **`Modules`**: Contains the main source code, including data models, database interactions, and utility functions.

For more details, refer to the :ref:`modules` section.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   modules
   config

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
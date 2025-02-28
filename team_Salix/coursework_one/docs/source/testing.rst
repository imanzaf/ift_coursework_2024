Testing Guide
=============

This guide explains how to run and maintain the test suite for the CSR Report Crawler and Storage System.

Test Dependencies
---------------

.. warning::
   Before running tests, you need to either:
   
   1. Run Pipeline A first to generate the required ``cleaned_url.csv`` file, or
   2. Use the provided mock data in ``tests/mock_data/`` directory

Running Tests
------------

Make sure you're in the correct directory:

.. code-block:: bash

   cd path/to/team_Salix/coursework_one

Option 1: Generate Required Test Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   poetry run python a_pipeline/modules/main.py
   poetry run python a_pipeline/modules/notfoundclean.py

Option 2: Use Mock Data (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cp tests/mock_data/cleaned_url.csv a_pipeline/aresult/

Running the Test Suite
--------------------

Basic test execution:

.. code-block:: bash

   poetry run pytest

Run with coverage report:

.. code-block:: bash

   poetry run pytest --cov=. tests/

Test specific components:

.. code-block:: bash

   poetry run pytest tests/a_pipeline/  # Test Pipeline A
   poetry run pytest tests/b_pipeline/  # Test Pipeline B

Detailed output:

.. code-block:: bash

   poetry run pytest -v

Test Suite Components
-------------------

The test suite includes:

* Unit tests for both pipelines
* Integration tests for the complete workflow
* Mock tests for external services
* Validation tests for PDF processing
* Error handling tests

.. note::
   Some tests use mock data to avoid dependencies on external services and long-running processes.
   This ensures tests can run quickly and reliably in any environment.

Test Configuration
----------------

The test configuration is managed through:

* ``pytest.ini``: General pytest configuration
* ``conftest.py``: Shared test fixtures and configuration
* ``tests/mock_data/``: Mock data for testing

Writing New Tests
---------------

When writing new tests:

1. Follow the existing test structure
2. Use appropriate fixtures from ``conftest.py``
3. Mock external services where appropriate
4. Include both positive and negative test cases
5. Document test requirements and assumptions

Test Coverage
-----------

We aim to maintain high test coverage:

* Core functionality: 90%+ coverage
* Utility functions: 80%+ coverage
* Error handlers: 95%+ coverage

Use coverage reports to identify areas needing additional tests:

.. code-block:: bash

   poetry run pytest --cov=. --cov-report=html tests/ 
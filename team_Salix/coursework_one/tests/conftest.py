"""
Common test fixtures and configurations for all tests.
"""

import os
import sys
import pytest
import tempfile
import pandas as pd
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

@pytest.fixture
def sample_data():
    """
    Fixture providing sample data for testing.
    """
    return {
        'companies': ['3M Company', 'Apple Inc', 'Microsoft Corporation'],
        'years': [2022, 2023, 2024]
    }

@pytest.fixture
def temp_dir():
    """
    Fixture providing a temporary directory for test files.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def sample_csv(temp_dir):
    """
    Fixture providing a sample CSV file for testing.
    """
    df = pd.DataFrame({
        'company': ['3M Company', 'Apple Inc'],
        'year': [2023, 2024],
        'url': ['http://example.com/3m.pdf', 'http://example.com/apple.pdf'],
        'source': ['website', 'website']
    })
    
    csv_path = os.path.join(temp_dir, 'test.csv')
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_config():
    """
    Fixture providing mock configuration for testing.
    """
    return {
        'minio': {
            'endpoint': 'http://localhost:9000',
            'access_key': 'test_key',
            'secret_key': 'test_secret',
            'bucket_name': 'test-bucket'
        },
        'postgres': {
            'host': 'localhost',
            'port': '5439',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
    }

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment with mock data."""
    # Get absolute paths
    base_dir = Path(project_root)
    mock_data_dir = base_dir / "tests/mock_data"
    aresult_dir = base_dir / "a_pipeline/aresult"
    bresult_dir = base_dir / "b_pipeline/bresult"
    
    # Create necessary directories
    mock_data_dir.mkdir(exist_ok=True)
    aresult_dir.mkdir(exist_ok=True, parents=True)
    bresult_dir.mkdir(exist_ok=True, parents=True)
    
    # Create mock cleaned_url.csv if it doesn't exist
    mock_csv_path = mock_data_dir / "cleaned_url.csv"
    if not mock_csv_path.exists():
        mock_data = {
            'company': ['Test Company'],
            'year': ['2024'],
            'url': ['http://example.com/test.pdf']
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(mock_csv_path, index=False)
    
    # Copy mock data to expected location
    import shutil
    shutil.copy(str(mock_csv_path), str(aresult_dir / "cleaned_url.csv"))
    
    yield
    
    # Cleanup after tests
    if (aresult_dir / "cleaned_url.csv").exists():
        os.remove(aresult_dir / "cleaned_url.csv")

# Keep existing fixtures below
@pytest.fixture
def sample_data():
    """
    Fixture providing sample data for testing.
    """
    return {
        'companies': ['3M Company', 'Apple Inc', 'Microsoft Corporation'],
        'years': [2022, 2023, 2024]
    }

@pytest.fixture
def temp_dir():
    """
    Fixture providing a temporary directory for test files.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def sample_csv(temp_dir):
    """
    Fixture providing a sample CSV file for testing.
    """
    df = pd.DataFrame({
        'company': ['3M Company', 'Apple Inc'],
        'year': [2023, 2024],
        'url': ['http://example.com/3m.pdf', 'http://example.com/apple.pdf'],
        'source': ['website', 'website']
    })
    
    csv_path = os.path.join(temp_dir, 'test.csv')
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_config():
    """
    Fixture providing mock configuration for testing.
    """
    return {
        'minio': {
            'endpoint': 'http://localhost:9000',
            'access_key': 'test_key',
            'secret_key': 'test_secret',
            'bucket_name': 'test-bucket'
        },
        'postgres': {
            'host': 'localhost',
            'port': '5439',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
    } 
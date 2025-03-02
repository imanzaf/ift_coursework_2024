"""
Tests for Pipeline B main module.
"""

import os
import pytest
import pandas as pd
from unittest.mock import patch, Mock, mock_open, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil
from tqdm.asyncio import tqdm
import aiohttp
import asyncio

# Module level patches
@pytest.fixture(autouse=True)
def mock_module_globals():
    """Mock module level globals to avoid initialization errors."""
    with patch('b_pipeline.modules.main.df', new=pd.DataFrame({
            'company': ['Test Company'],
            'year': [2024],
            'url': ['http://example.com/test.pdf']
        })), \
        patch('b_pipeline.modules.main.CSV_PATH', new='mock_csv_path'), \
        patch('b_pipeline.modules.main.DOWNLOAD_ROOT', new='mock_download_root'):
        yield

@pytest.fixture(scope="session")
def mock_data_dir():
    """Create a temporary directory for mock data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture(scope="session")
def mock_csv_file(mock_data_dir):
    """Create a mock CSV file with test data."""
    mock_data = pd.DataFrame({
        'company': ['Test Company'],
        'year': [2024],
        'url': ['http://example.com/test.pdf']
    })
    
    csv_path = mock_data_dir / "cleaned_url.csv"
    mock_data.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture(autouse=True)
def mock_environment(mock_csv_file, tmp_path, monkeypatch):
    """Mock environment variables and module attributes."""
    # Set environment variables
    monkeypatch.setenv("CSV_PATH", str(mock_csv_file))
    download_path = str(tmp_path / "downloads")
    monkeypatch.setenv("DOWNLOAD_PATH", download_path)
    
    # Create the download directory
    downloads_dir = Path(download_path)
    downloads_dir.mkdir(exist_ok=True)
    
    yield

class MockContent:
    def __init__(self, content=b"test data"):
        self._content = content
        self._chunks = [content[i:i+1024] for i in range(0, len(content), 1024)]
        
    async def iter_chunked(self, chunk_size):
        for chunk in self._chunks:
            yield chunk
            
    async def read(self):
        return self._content

class MockResponse:
    def __init__(self, status=200, content=b"test data", content_length=1024):
        self.status = status
        self.content = MockContent(content)
        self.headers = {"content-length": str(content_length)}

class MockGet:
    def __init__(self, response):
        self.response = response
        
    async def __aenter__(self):
        return self.response
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

class MockClientSession:
    def __init__(self, response=None):
        self.response = response or MockResponse()
        
    def get(self, url, **kwargs):
        return MockGet(self.response)

@pytest.mark.asyncio
async def test_download_pdf(tmp_path):
    from b_pipeline.modules.main import download_pdf
    
    # Create test data
    company = "Test Company"
    year = "2024"
    url = "http://example.com/test.pdf"
    row = pd.Series({'company': company, 'year': year, 'url': url})
    
    # Test successful download
    mock_session = MockClientSession()
    progress = tqdm(total=1)
    
    with patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', mock_open()) as mock_file:
        result = await download_pdf(mock_session, row, progress)
        assert result is True, "Download should succeed"
        mock_makedirs.assert_called()
        mock_file.assert_called()

    # Test failed download (HTTP error)
    mock_session = MockClientSession(MockResponse(status=404))
    with patch('os.makedirs'), patch('builtins.open', mock_open()):
        result = await download_pdf(mock_session, row, progress)
        assert result is False, "Download should fail with 404"

    # Test failed download (Network error)
    async def raise_error(*args, **kwargs):
        raise aiohttp.ClientError("Network error")
    
    mock_session = MockClientSession()
    mock_session.get = raise_error
    with patch('os.makedirs'), patch('builtins.open', mock_open()):
        result = await download_pdf(mock_session, row, progress)
        assert result is False, "Download should fail with network error"

@patch('builtins.open', new_callable=mock_open)
def test_log_failed_download(mock_file):
    from b_pipeline.modules.main import log_failed_download
    
    # Test data
    url = "http://example.com/test.pdf"
    reason = "HTTP 404"
    
    # Call function
    log_failed_download(url, reason)
    
    # Verify file was opened correctly
    mock_file.assert_called_once_with("download_failed.txt", "a", encoding="utf-8")
    
    # Verify write call
    mock_file().write.assert_called_once_with(f"Failed: {url} | Reason: {reason}\n")

@patch('builtins.open', new_callable=mock_open)
def test_log_statistics(mock_file):
    from b_pipeline.modules.main import log_statistics
    
    # Test data
    stats_info = "Test Statistics"
    
    # Call function
    log_statistics(stats_info)
    
    # Verify file was opened correctly
    mock_file.assert_called_once_with("download_failed.txt", "a", encoding="utf-8")
    
    # Verify write calls
    expected_calls = [
        "\n" + "="*50 + "\n",
        "Download Statistics\n",
        "="*50 + "\n",
        stats_info,
        "\n" + "="*50 + "\n"
    ]
    
    assert mock_file().write.call_count == len(expected_calls)
    for call, expected in zip(mock_file().write.call_args_list, expected_calls):
        assert call[0][0] == expected 
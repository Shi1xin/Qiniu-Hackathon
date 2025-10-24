"""
Pytest configuration and fixtures for CLI Navigation Tool tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_playwright():
    """Mock Playwright browser automation."""
    with patch('playwright.sync_api.sync_playwright') as mock:
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        mock_instance = Mock()
        mock_instance.chromium.launch.return_value = mock_browser

        yield mock_instance.return_value


@pytest.fixture
def sample_query():
    """Sample navigation query for testing."""
    return "从北京到上海"


@pytest.fixture
def sample_location_entities():
    """Sample location entities for testing."""
    return {
        "origin": {"name": "北京", "type": "city", "confidence": 0.95},
        "destination": {"name": "上海", "type": "city", "confidence": 0.95}
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    return {
        "GOOGLE_API_KEY": "test-google-api-key",
        "OPENAI_API_KEY": "test-openai-api-key",
        "ANTHROPIC_API_KEY": "test-anthropic-api-key",
        "NAV_TOOL_DEFAULT_BROWSER": "chromium",
        "NAV_TOOL_HEADLESS_MODE": "true",
        "NAV_TOOL_TIMEOUT_MS": "10000"
    }


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clean environment variables before each test."""
    # Clear all NAV_TOOL_* and API key environment variables
    for key in list(monkeypatch._environ):
        if key.startswith("NAV_TOOL_") or key.endswith("_API_KEY"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def performance_timing():
    """Mock performance timing data."""
    return {
        "parsing_time_ms": 500,
        "url_construction_time_ms": 100,
        "browser_launch_time_ms": 2000,
        "navigation_time_ms": 1500,
        "total_time_ms": 4100
    }
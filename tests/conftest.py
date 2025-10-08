"""
Shared test fixtures and mocks for YouTube Transcript Service tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any
import os

from app import app


@pytest.fixture
def client():
    """
    FastAPI TestClient for making HTTP requests to the API
    """
    return TestClient(app)


@pytest.fixture
def sample_transcript_data() -> List[Dict[str, Any]]:
    """
    Sample transcript data for testing
    Returns a list of transcript segments
    """
    return [
        {"text": "Hello", "start": 0.0, "duration": 1.5},
        {"text": "world", "start": 1.5, "duration": 1.0},
        {"text": "this is a test", "start": 2.5, "duration": 2.0}
    ]


@pytest.fixture
def sample_transcript_long() -> List[Dict[str, Any]]:
    """
    Longer transcript data for testing performance
    """
    return [
        {"text": f"Segment {i}", "start": float(i), "duration": 1.0}
        for i in range(100)
    ]


@pytest.fixture
def sample_transcript_spanish() -> List[Dict[str, Any]]:
    """
    Spanish transcript data for language testing
    """
    return [
        {"text": "Hola", "start": 0.0, "duration": 1.0},
        {"text": "mundo", "start": 1.0, "duration": 1.0},
        {"text": "esto es una prueba", "start": 2.0, "duration": 2.0}
    ]


@pytest.fixture
def sample_transcript_unicode() -> List[Dict[str, Any]]:
    """
    Transcript with unicode characters and emojis
    """
    return [
        {"text": "Hello 👋", "start": 0.0, "duration": 1.0},
        {"text": "世界", "start": 1.0, "duration": 1.0},
        {"text": "Привет", "start": 2.0, "duration": 1.0}
    ]


@pytest.fixture
def mock_youtube_api():
    """
    Mock YouTubeTranscriptApi instance for testing
    """
    mock_api = Mock()
    mock_fetched = Mock()
    mock_api.fetch.return_value = mock_fetched
    return mock_api, mock_fetched


@pytest.fixture
def mock_env_with_proxy(monkeypatch):
    """
    Set environment variables with proxy configuration
    """
    monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
    monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "testpass")
    monkeypatch.setenv("PROXY_LOCATIONS", "")
    yield
    # Cleanup happens automatically with monkeypatch


@pytest.fixture
def mock_env_without_proxy(monkeypatch):
    """
    Set environment variables without proxy configuration
    """
    monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "")
    monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "")
    monkeypatch.setenv("PROXY_LOCATIONS", "")
    yield


@pytest.fixture
def mock_env_with_proxy_locations(monkeypatch):
    """
    Set environment variables with proxy and location filtering
    """
    monkeypatch.setenv("WEBSHARE_PROXY_USERNAME", "testuser")
    monkeypatch.setenv("WEBSHARE_PROXY_PASSWORD", "testpass")
    monkeypatch.setenv("PROXY_LOCATIONS", "us,de,gb")
    yield


@pytest.fixture
def mock_successful_extraction(monkeypatch, sample_transcript_data):
    """
    Mock extract_transcript to return successful response
    """
    def mock_extract(video_id: str, language: str = "en"):
        transcript_text = " ".join([seg["text"] for seg in sample_transcript_data])
        return True, transcript_text, sample_transcript_data
    
    import app
    monkeypatch.setattr(app, "extract_transcript", mock_extract)
    return sample_transcript_data


@pytest.fixture
def mock_failed_extraction(monkeypatch):
    """
    Mock extract_transcript to return failed response
    """
    def mock_extract(video_id: str, language: str = "en"):
        return False, None, None
    
    import app
    monkeypatch.setattr(app, "extract_transcript", mock_extract)


@pytest.fixture
def valid_video_id() -> str:
    """
    A valid sample video ID for testing
    """
    return "dQw4w9WgXcQ"


@pytest.fixture
def invalid_video_id() -> str:
    """
    An invalid video ID for testing error cases
    """
    return "invalid_video_123"

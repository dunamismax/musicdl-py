"""Tests for download functionality."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from musicdl.core.downloader import YTDLPDownloader
from musicdl.core.models import AppConfig, TrackItem, TrackStatus


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = AppConfig()
    config.music_dir = Path("/tmp/test_music")
    return config


@pytest.fixture
def track_item():
    """Create a test track item."""
    return TrackItem(
        artist="Test Artist",
        title="Test Song",
        query="Test Artist - Test Song",
        target_stub="Test Artist - Test Song"
    )


def test_downloader_initialization(mock_config):
    """Test downloader initialization."""
    downloader = YTDLPDownloader(mock_config)
    assert downloader.config == mock_config
    assert downloader.progress_callback is None


def test_sanitize_filename():
    """Test filename sanitization."""
    from musicdl.core.downloader import YTDLPDownloader
    
    downloader = YTDLPDownloader(AppConfig())
    
    # Test basic sanitization
    result = downloader._sanitize_filename("Test / Song * Title")
    assert "/" not in result
    assert "*" not in result
    
    # Test empty input
    result = downloader._sanitize_filename("")
    assert result == "audio"


@patch('musicdl.core.downloader.YoutubeDL')
def test_search_track(mock_ytdl, mock_config, track_item):
    """Test track searching."""
    # Mock YoutubeDL response
    mock_instance = MagicMock()
    mock_ytdl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        "entries": [{
            "title": "Test Song",
            "webpage_url": "https://youtube.com/watch?v=test",
            "duration": 240
        }]
    }
    
    downloader = YTDLPDownloader(mock_config)
    result = downloader.search_track(track_item)
    
    assert result is not None
    assert result.title == "Test Song"
    assert result.url == "https://youtube.com/watch?v=test"
    assert result.duration == 240


def test_track_item_display_name():
    """Test track item display name generation."""
    # Test with both artist and title
    track = TrackItem(
        artist="Test Artist",
        title="Test Song", 
        query="Test Artist - Test Song",
        target_stub="Test Artist - Test Song"
    )
    assert track.display_name == "Test Artist - Test Song"
    
    # Test with title only
    track = TrackItem(
        artist="",
        title="Test Song",
        query="Test Song", 
        target_stub="Test Song"
    )
    assert track.display_name == "Test Song"
    
    # Test with artist only
    track = TrackItem(
        artist="Test Artist",
        title="",
        query="Test Artist",
        target_stub="Test Artist" 
    )
    assert track.display_name == "Test Artist"
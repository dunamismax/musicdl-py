"""Tests for URL processing functionality."""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch

from musicdl.core.url_processor import URLProcessor, URLParsingError
from musicdl.core.models import TrackItem


@pytest.fixture
def url_processor():
    """Create URL processor instance."""
    return URLProcessor()


def test_youtube_url_validation(url_processor):
    """Test YouTube URL validation."""
    # Valid URLs
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
    ]
    
    for url in valid_urls:
        assert url_processor.is_valid_youtube_url(url), f"Should be valid: {url}"
    
    # Invalid URLs
    invalid_urls = [
        "https://vimeo.com/123456",
        "https://facebook.com/video",
        "not_a_url",
        "",
        "https://youtube.com/fake",
        "javascript:alert('xss')",
    ]
    
    for url in invalid_urls:
        assert not url_processor.is_valid_youtube_url(url), f"Should be invalid: {url}"


def test_playlist_url_detection(url_processor):
    """Test playlist URL detection."""
    playlist_urls = [
        "https://www.youtube.com/playlist?list=PLDcmYGGuVabdqQwe234",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLDcmYGGuVabdqQwe234",
        "https://youtube.com/playlist?list=PLDcmYGGuVabdqQwe234",
    ]
    
    for url in playlist_urls:
        assert url_processor.is_playlist_url(url), f"Should be playlist: {url}"
    
    non_playlist_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "invalid_url",
    ]
    
    for url in non_playlist_urls:
        assert not url_processor.is_playlist_url(url), f"Should not be playlist: {url}"


def test_video_id_extraction(url_processor):
    """Test video ID extraction."""
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ]
    
    for url, expected_id in test_cases:
        extracted_id = url_processor.extract_video_id(url)
        assert extracted_id == expected_id, f"URL {url} should extract {expected_id}"


def test_playlist_id_extraction(url_processor):
    """Test playlist ID extraction."""
    test_cases = [
        ("https://www.youtube.com/playlist?list=PLDcmYGGuVabdqQwe234", "PLDcmYGGuVabdqQwe234"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLDcmYGGuVabdqQwe234", "PLDcmYGGuVabdqQwe234"),
    ]
    
    for url, expected_id in test_cases:
        extracted_id = url_processor.extract_playlist_id(url)
        assert extracted_id == expected_id, f"URL {url} should extract {expected_id}"


def test_url_normalization(url_processor):
    """Test URL normalization."""
    test_cases = [
        ("https://youtu.be/dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ]
    
    for original, expected in test_cases:
        normalized = url_processor.normalize_youtube_url(original)
        assert normalized == expected, f"URL {original} should normalize to {expected}"


def test_track_creation_from_url(url_processor):
    """Test creating track items from URLs."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Test without title override
    track = url_processor.create_track_from_url(url)
    assert track.url == url
    assert track.artist == ""
    assert track.title == "dQw4w9WgXcQ"  # Falls back to video ID
    
    # Test with title override
    track = url_processor.create_track_from_url(url, "Custom Title")
    assert track.url == url
    assert track.title == "Custom Title"


def test_text_file_validation(url_processor):
    """Test text file validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("https://www.youtube.com/watch?v=dQw4w9WgXcQ\\n")
        f.write("# This is a comment\\n")
        f.write("\\n")  # Empty line
        f.write("https://youtu.be/another_id\\n")
        f.write("invalid_url\\n")
        temp_path = Path(f.name)
    
    try:
        valid_count, total_lines, errors = url_processor.validate_text_file(temp_path)
        
        assert total_lines == 5
        assert valid_count == 2
        assert len(errors) == 1  # One invalid URL
        assert "invalid_url" in errors[0]
        
    finally:
        temp_path.unlink()


def test_load_urls_from_text_file(url_processor):
    """Test loading URLs from text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("https://www.youtube.com/watch?v=dQw4w9WgXcQ\\n")
        f.write("# Comment line\\n")
        f.write("https://youtu.be/another_id\\n")
        temp_path = Path(f.name)
    
    try:
        tracks = url_processor.load_urls_from_text_file(temp_path)
        
        assert len(tracks) == 2
        assert tracks[0].url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert tracks[1].url == "https://youtu.be/another_id"
        
    finally:
        temp_path.unlink()


def test_invalid_file_handling(url_processor):
    """Test handling of invalid files."""
    # Test non-existent file
    with pytest.raises(URLParsingError):
        url_processor.validate_text_file(Path("non_existent.txt"))
    
    # Test directory instead of file
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(URLParsingError):
            url_processor.validate_text_file(Path(temp_dir))


def test_security_validation(url_processor):
    """Test security validation for file paths."""
    dangerous_paths = [
        Path("../../../etc/passwd"),
        Path("..\\..\\..\\windows\\system32\\config\\sam"),
        Path("~/.ssh/id_rsa"),
    ]
    
    for path in dangerous_paths:
        with pytest.raises(URLParsingError):
            url_processor.validate_text_file(path)


def test_malformed_urls(url_processor):
    """Test handling of malformed URLs."""
    malformed_urls = [
        "javascript:alert('xss')",
        "data:text/html,<script>alert('xss')</script>",
        "file:///etc/passwd",
        "ftp://malicious.com/file",
    ]
    
    for url in malformed_urls:
        assert not url_processor.is_valid_youtube_url(url)


def test_empty_content_handling(url_processor):
    """Test handling of empty or whitespace-only content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("   \\n")  # Just whitespace
        f.write("\\n\\n")  # Empty lines
        temp_path = Path(f.name)
    
    try:
        valid_count, total_lines, errors = url_processor.validate_text_file(temp_path)
        assert valid_count == 0
        assert total_lines == 3
        assert len(errors) == 0  # Empty lines should be silently ignored
        
    finally:
        temp_path.unlink()
"""Tests for file utility functions."""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch, mock_open

from musicdl.utils.file_utils import (
    detect_file_encoding,
    read_text_file_safe,
    detect_csv_encoding_and_content,
    validate_file_path,
    FileEncodingError,
)


def test_detect_file_encoding():
    """Test file encoding detection."""
    # Test UTF-8 file
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write("Hello, world! 🌍")
        temp_path = Path(f.name)
    
    try:
        encoding = detect_file_encoding(temp_path)
        assert encoding in ['utf-8', 'utf-8-sig']
    finally:
        temp_path.unlink()
    
    # Test Latin-1 file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write("café".encode('latin-1'))
        temp_path = Path(f.name)
    
    try:
        encoding = detect_file_encoding(temp_path)
        assert encoding in ['latin-1', 'cp1252', 'iso-8859-1']
    finally:
        temp_path.unlink()


def test_detect_file_encoding_nonexistent():
    """Test encoding detection with non-existent file."""
    with pytest.raises(FileEncodingError, match="File not found"):
        detect_file_encoding(Path("non_existent_file.txt"))


def test_detect_file_encoding_directory():
    """Test encoding detection with directory instead of file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(FileEncodingError, match="Path is not a file"):
            detect_file_encoding(Path(temp_dir))


def test_read_text_file_safe():
    """Test safe text file reading."""
    test_content = "Hello, world! 🌍\\nSecond line"
    
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        content = read_text_file_safe(temp_path)
        assert content == test_content
    finally:
        temp_path.unlink()


def test_read_text_file_safe_with_encoding():
    """Test safe text file reading with specific encoding."""
    test_content = "café"
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(test_content.encode('latin-1'))
        temp_path = Path(f.name)
    
    try:
        content = read_text_file_safe(temp_path, encoding='latin-1')
        assert content == test_content
    finally:
        temp_path.unlink()


def test_read_text_file_safe_corrupted():
    """Test safe text file reading with corrupted file."""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(b'\\xff\\xfe\\x00\\x00invalid utf-8')  # Invalid UTF-8 sequence
        temp_path = Path(f.name)
    
    try:
        # Should still work with error handling
        content = read_text_file_safe(temp_path)
        assert content is not None  # Should not raise exception
    finally:
        temp_path.unlink()


def test_detect_csv_encoding_and_content():
    """Test CSV encoding detection and content sampling."""
    csv_content = "Artist,Title\\nTest Artist,Test Song\\nAnother,Track"
    
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = Path(f.name)
    
    try:
        encoding, sample = detect_csv_encoding_and_content(temp_path)
        assert encoding in ['utf-8', 'utf-8-sig']
        assert "Artist,Title" in sample
        assert "Test Artist,Test Song" in sample
    finally:
        temp_path.unlink()


def test_validate_file_path():
    """Test file path validation."""
    # Create a real file for testing
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Valid existing file
        assert validate_file_path(temp_path, must_exist=True)
        
        # Valid path that doesn't need to exist
        non_existent = temp_path.parent / "new_file.txt"
        assert validate_file_path(non_existent, must_exist=False)
        
    finally:
        temp_path.unlink()


def test_validate_file_path_security():
    """Test file path security validation."""
    dangerous_paths = [
        Path("../../../etc/passwd"),
        Path("..\\\\..\\\\..\\\\windows\\\\system32"),
        Path("~/../../etc/passwd"),
    ]
    
    for path in dangerous_paths:
        # Should detect path traversal attempts
        assert not validate_file_path(path, must_exist=False)


def test_validate_file_path_nonexistent():
    """Test validation of non-existent files when existence is required."""
    assert not validate_file_path(Path("definitely_does_not_exist.txt"), must_exist=True)


def test_validate_file_path_directory():
    """Test validation when path is a directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir)
        # Directory should fail validation when we need a file
        assert not validate_file_path(path, must_exist=True)


@patch('builtins.open', mock_open(read_data=b'\\xff\\xfe'))
def test_encoding_detection_fallback():
    """Test encoding detection fallback behavior."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Should fallback to utf-8 when detection fails
        encoding = detect_file_encoding(temp_path)
        assert encoding == 'utf-8'
    finally:
        temp_path.unlink()


def test_file_utils_error_handling():
    """Test comprehensive error handling in file utilities."""
    
    # Test with permission denied (mock)
    with patch('pathlib.Path.open', side_effect=PermissionError("Access denied")):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(FileEncodingError):
                read_text_file_safe(temp_path)
        finally:
            temp_path.unlink()


def test_large_file_handling():
    """Test handling of large files with limited sampling."""
    large_content = "A" * 100000  # 100KB content
    
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write(large_content)
        temp_path = Path(f.name)
    
    try:
        # Should handle large files gracefully with sampling
        encoding, sample = detect_csv_encoding_and_content(temp_path, sample_bytes=1024)
        assert encoding in ['utf-8', 'utf-8-sig']
        assert len(sample) <= 1024 + 100  # Some buffer for decoding
    finally:
        temp_path.unlink()


def test_unicode_edge_cases():
    """Test handling of various Unicode edge cases."""
    test_cases = [
        ("UTF-8 BOM", "\\ufeffHello, world!"),
        ("Emoji content", "Hello 👋 World 🌍"),
        ("Mixed scripts", "Hello мир 世界"),
        ("Control chars", "Line1\\r\\nLine2\\tTab"),
    ]
    
    for case_name, content in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            read_content = read_text_file_safe(temp_path)
            # Should handle all Unicode cases correctly
            assert read_content == content, f"Failed for {case_name}"
        finally:
            temp_path.unlink()
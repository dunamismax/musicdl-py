"""File utilities for encoding detection and safe file operations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class FileEncodingError(Exception):
    """Raised when file encoding detection fails."""


def detect_file_encoding(file_path: Path, sample_bytes: int = 64 * 1024) -> str:
    """
    Detect the encoding of a text file.
    
    Args:
        file_path: Path to the file to analyze
        sample_bytes: Number of bytes to read for detection
        
    Returns:
        The detected encoding string
        
    Raises:
        FileEncodingError: If encoding detection fails
    """
    if not file_path.exists():
        raise FileEncodingError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise FileEncodingError(f"Path is not a file: {file_path}")
    
    # Common encodings to try, in order of preference
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]
    
    for encoding in encodings:
        try:
            with file_path.open("rb") as f:
                raw_data = f.read(sample_bytes)
            
            # Test if we can decode the sample
            raw_data.decode(encoding)
            
            # If successful, validate with a larger sample for confidence
            try:
                with file_path.open("r", encoding=encoding) as f:
                    f.read(1024)  # Read a small portion to validate
                return encoding
            except UnicodeDecodeError:
                continue
                
        except (UnicodeDecodeError, LookupError):
            continue
    
    # If no encoding worked, fallback to utf-8 with error handling
    logger.warning(f"Could not detect encoding for {file_path}, using utf-8 with error handling")
    return "utf-8"


def read_text_file_safe(file_path: Path, encoding: Optional[str] = None) -> str:
    """
    Safely read a text file with automatic encoding detection.
    
    Args:
        file_path: Path to the file to read
        encoding: Optional specific encoding to use
        
    Returns:
        The file contents as a string
        
    Raises:
        FileEncodingError: If the file cannot be read
    """
    if encoding is None:
        encoding = detect_file_encoding(file_path)
    
    try:
        return file_path.read_text(encoding=encoding)
    except UnicodeDecodeError as e:
        # Try with error handling
        try:
            return file_path.read_text(encoding=encoding, errors="replace")
        except Exception as fallback_error:
            raise FileEncodingError(
                f"Failed to read file {file_path} with encoding {encoding}: {fallback_error}"
            ) from e


def detect_csv_encoding_and_content(
    file_path: Path, sample_bytes: int = 64 * 1024
) -> Tuple[str, str]:
    """
    Detect CSV file encoding and return a sample of content for analysis.
    
    Args:
        file_path: Path to the CSV file
        sample_bytes: Number of bytes to read for detection
        
    Returns:
        Tuple of (encoding, sample_content)
        
    Raises:
        FileEncodingError: If encoding detection fails
    """
    encoding = detect_file_encoding(file_path, sample_bytes)
    
    try:
        with file_path.open("rb") as f:
            raw_sample = f.read(sample_bytes)
        
        sample_content = raw_sample.decode(encoding, errors="replace")
        return encoding, sample_content
        
    except Exception as e:
        raise FileEncodingError(f"Failed to read CSV sample: {e}") from e


def validate_file_path(file_path: Path, must_exist: bool = True) -> bool:
    """
    Validate that a file path is safe to use.
    
    Args:
        file_path: Path to validate
        must_exist: Whether the file must exist
        
    Returns:
        True if the path is valid and safe
    """
    try:
        # Resolve the path to detect any traversal attempts
        resolved_path = file_path.resolve()
        
        # Basic security checks
        if '..' in str(file_path):
            logger.warning(f"Path contains traversal attempt: {file_path}")
            return False
        
        if must_exist:
            if not resolved_path.exists():
                logger.warning(f"File does not exist: {resolved_path}")
                return False
            
            if not resolved_path.is_file():
                logger.warning(f"Path is not a file: {resolved_path}")
                return False
        
        return True
        
    except (OSError, ValueError) as e:
        logger.warning(f"Path validation failed for {file_path}: {e}")
        return False
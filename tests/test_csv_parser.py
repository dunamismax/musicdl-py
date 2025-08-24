"""Tests for CSV parsing functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch

from musicdl.core.csv_parser import CSVParser, CSVParsingError


def test_csv_parser_initialization():
    """Test CSV parser initialization."""
    parser = CSVParser()
    assert parser.max_preview_rows == 200
    assert parser.sample_bytes == 64 * 1024


def test_parse_artist_title_from_single():
    """Test parsing artist and title from single column."""
    parser = CSVParser()
    
    # Test with dash separator
    artist, title = parser.parse_artist_title_from_single("Artist Name - Song Title")
    assert artist == "Artist Name"
    assert title == "Song Title"
    
    # Test with em dash
    artist, title = parser.parse_artist_title_from_single("Artist Name — Song Title")
    assert artist == "Artist Name"
    assert title == "Song Title"
    
    # Test with quoted pattern
    artist, title = parser.parse_artist_title_from_single('Artist Name "Song Title"')
    assert artist == "Artist Name"
    assert title == "Song Title"
    
    # Test fallback (title only)
    artist, title = parser.parse_artist_title_from_single("Just a Title")
    assert artist == ""
    assert title == "Just a Title"


def test_csv_parsing_error():
    """Test CSV parsing error handling."""
    parser = CSVParser()
    
    # Test with non-existent file
    with pytest.raises(CSVParsingError):
        parser.load_csv(Path("non_existent_file.csv"))


@pytest.mark.asyncio
async def test_csv_detection():
    """Test CSV detection with mock data."""
    # This would require creating test CSV files
    # For now, just test that the class can be instantiated
    parser = CSVParser()
    assert parser is not None
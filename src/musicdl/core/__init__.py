"""Core functionality for MusicDL."""

from .csv_parser import CSVDetection, CSVParser
from .downloader import TrackItem, YTDLPDownloader
from .models import AppConfig, DownloadResult, SearchResult, TrackStatus
from .url_processor import URLProcessor

__all__ = [
    "CSVDetection",
    "CSVParser",
    "TrackItem",
    "YTDLPDownloader",
    "URLProcessor",
    "AppConfig",
    "DownloadResult",
    "SearchResult",
    "TrackStatus",
]

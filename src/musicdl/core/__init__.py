"""Core functionality for MusicDL."""

from .csv_parser import CSVDetection, CSVParser
from .downloader import TrackItem, YTDLPDownloader
from .models import AppConfig, DownloadResult, SearchResult, TrackStatus

__all__ = [
    "CSVDetection",
    "CSVParser", 
    "TrackItem",
    "YTDLPDownloader",
    "AppConfig",
    "DownloadResult",
    "SearchResult",
    "TrackStatus",
]
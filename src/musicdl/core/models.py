"""Data models for MusicDL."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class TrackStatus(str, Enum):
    """Status of a track download."""

    PENDING = "pending"
    SEARCHING = "searching"
    FOUND = "found"
    DOWNLOADING = "downloading"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


class AppConfig(BaseModel):
    """Application configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # Directories
    music_dir: Path = Path("~/Downloads/MusicDL Downloads").expanduser()
    cache_dir: Path = Path(".cache")
    logs_dir: Path = Path("logs")

    # Download settings
    max_concurrent_downloads: int = 3
    audio_format: str = "bestaudio[ext=webm][acodec=opus]/bestaudio/best"
    bitrate: str = "best"
    output_template: str = "{artist} - {title}.%(ext)s"
    overwrite_files: bool = True

    # CSV processing
    max_preview_rows: int = 200
    encoding: str = "utf-8-sig"

    # UI settings
    show_clock: bool = True
    theme: str = "dark"

    # Advanced settings
    user_agent: str | None = None
    extract_flat: bool = False
    write_info_json: bool = False
    write_thumbnail: bool = False

    def ensure_directories(self) -> None:
        """Create necessary directories."""
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class CSVDetection:
    """Result of CSV file analysis."""

    headers: list[str]
    artist_col: str | None
    track_col: str | None
    single_title_col: str | None
    dialect: csv.Dialect
    preview_rows: list[dict[str, str]]
    encoding: str = "utf-8-sig"

    @property
    def is_single_column_mode(self) -> bool:
        """Check if using single column for artist-title parsing."""
        return self.single_title_col is not None

    @property
    def has_artist_track_columns(self) -> bool:
        """Check if has separate artist and track columns."""
        return self.artist_col is not None and self.track_col is not None


@dataclass
class TrackItem:
    """A track to be downloaded."""

    artist: str
    title: str
    query: str
    target_stub: str  # Filename without extension
    status: TrackStatus = TrackStatus.PENDING
    url: str | None = None
    result_path: str | None = None
    error: str | None = None
    duration: float | None = None
    filesize: int | None = None

    @property
    def display_name(self) -> str:
        """Human-readable track name."""
        if self.artist and self.title:
            return f"{self.artist} - {self.title}"
        return self.title or self.artist or "Unknown"

    def to_dict(self) -> dict[str, str | float | int | None]:
        """Convert to dictionary for JSON serialization."""
        return {
            "artist": self.artist,
            "title": self.title,
            "query": self.query,
            "status": self.status.value,
            "url": self.url,
            "result_path": self.result_path,
            "error": self.error,
            "duration": self.duration,
            "filesize": self.filesize,
        }


class SearchResult(BaseModel):
    """Result from searching for a track."""

    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    duration: float | None = None
    uploader: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    upload_date: str | None = None


class DownloadResult(BaseModel):
    """Result from downloading a track."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    file_path: Path | None = None
    error_message: str | None = None
    duration: float | None = None
    filesize: int | None = None
    format_info: dict[str, str] | None = None

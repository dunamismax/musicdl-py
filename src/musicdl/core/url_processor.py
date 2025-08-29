"""URL processing functionality for YouTube links and text files."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ..utils.file_utils import read_text_file_safe, validate_file_path
from .models import TrackItem

logger = logging.getLogger(__name__)

# YouTube URL patterns
YOUTUBE_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
    r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)",
    r"(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)",
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)",
    r"(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
]

# Compiled regex patterns
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in YOUTUBE_PATTERNS]


class URLParsingError(Exception):
    """Raised when URL parsing fails."""


class URLProcessor:
    """Handles URL processing for single links and text files."""

    def __init__(self) -> None:
        pass

    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        url = url.strip()
        if not url:
            return False

        for pattern in COMPILED_PATTERNS:
            if pattern.search(url):
                return True

        return False

    def extract_video_id(self, url: str) -> str | None:
        """Extract video ID from YouTube URL."""
        url = url.strip()

        for pattern in COMPILED_PATTERNS:
            match = pattern.search(url)
            if match:
                return match.group(1)

        return None

    def normalize_youtube_url(self, url: str) -> str | None:
        """Normalize YouTube URL to standard format."""
        video_id = self.extract_video_id(url)
        if not video_id:
            return None

        return f"https://www.youtube.com/watch?v={video_id}"

    def create_track_from_url(
        self, url: str, title_override: str | None = None
    ) -> TrackItem | None:
        """Create a TrackItem from a YouTube URL."""

        if not self.is_valid_youtube_url(url):
            logger.warning(f"Invalid YouTube URL: {url}")
            return None

        normalized_url = self.normalize_youtube_url(url)
        if not normalized_url:
            logger.warning(f"Could not normalize URL: {url}")
            return None

        # Use title override or extract from URL if possible
        title = title_override or self._extract_title_from_url(url) or "YouTube Video"

        return TrackItem(
            artist="",
            title=title,
            query=title,
            target_stub=title,
            url=normalized_url,
        )

    def _extract_title_from_url(self, url: str) -> str | None:
        """Try to extract title from URL query parameters."""
        # This is a basic implementation - in practice, we'd need to
        # fetch the actual video title from YouTube
        try:
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(url)
            if parsed.query:
                params = parse_qs(parsed.query)
                if "title" in params:
                    return params["title"][0]
        except Exception:
            pass

        return None

    def load_urls_from_text_file(self, file_path: Path) -> list[TrackItem]:
        """Load YouTube URLs from a text file."""

        if not file_path.exists():
            raise URLParsingError(f"Text file not found: {file_path}")

        if not file_path.is_file():
            raise URLParsingError(f"Path is not a file: {file_path}")

        tracks: list[TrackItem] = []
        seen_urls: set[str] = set()

        # Validate file path for security
        if not validate_file_path(file_path, must_exist=True):
            raise URLParsingError(f"Invalid or unsafe file path: {file_path}")

        try:
            # Use consolidated file reading with encoding detection
            content = read_text_file_safe(file_path)

            lines = content.strip().split("\n")

        except (OSError, UnicodeError) as e:
            raise URLParsingError(f"Failed to read or decode text file: {e}") from e
        except Exception as e:
            raise URLParsingError(f"Unexpected error reading text file: {e}") from e

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            # Check if line contains a YouTube URL
            if not self.is_valid_youtube_url(line):
                logger.warning(f"Line {line_num}: Not a valid YouTube URL: {line}")
                continue

            # Normalize URL and check for duplicates
            normalized_url = self.normalize_youtube_url(line)
            if not normalized_url:
                logger.warning(f"Line {line_num}: Could not normalize URL: {line}")
                continue

            if normalized_url in seen_urls:
                logger.warning(f"Line {line_num}: Duplicate URL skipped: {line}")
                continue

            seen_urls.add(normalized_url)

            # Create track item
            track = self.create_track_from_url(normalized_url)
            if track:
                # Add line number for reference
                track.query = f"Line {line_num}: {track.title}"
                tracks.append(track)
            else:
                logger.warning(
                    f"Line {line_num}: Failed to create track from URL: {line}"
                )

        if not tracks:
            raise URLParsingError("No valid YouTube URLs found in file")

        logger.info(f"Loaded {len(tracks)} valid URLs from {file_path}")
        return tracks

    def validate_text_file(self, file_path: Path) -> tuple[int, int, list[str]]:
        """Validate text file and return statistics.

        Returns:
            tuple: (valid_urls, total_lines, errors)
        """

        if not file_path.exists():
            return 0, 0, ["File not found"]

        errors: list[str] = []
        valid_urls = 0
        total_lines = 0

        try:
            # Try to read with different encodings
            content = None
            for encoding in ["utf-8-sig", "utf-8", "latin-1"]:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                errors.append("Could not decode file")
                return 0, 0, errors

            lines = content.strip().split("\n")

        except Exception as e:
            errors.append(f"Failed to read file: {e}")
            return 0, 0, errors

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            total_lines += 1

            # Skip empty lines and comments
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            if self.is_valid_youtube_url(line):
                valid_urls += 1
            else:
                errors.append(f"Line {line_num}: Invalid YouTube URL")

        return valid_urls, total_lines, errors

    def is_playlist_url(self, url: str) -> bool:
        """Check if URL is a YouTube playlist URL."""
        return "playlist" in url.lower() and "list=" in url

    def extract_playlist_id(self, url: str) -> str | None:
        """Extract playlist ID from YouTube playlist URL."""
        match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
        return match.group(1) if match else None

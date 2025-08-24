"""YouTube download functionality using yt-dlp."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import imageio_ffmpeg
from yt_dlp import YoutubeDL
from yt_dlp.utils import sanitize_filename

from .models import AppConfig, DownloadResult, SearchResult, TrackItem, TrackStatus

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Raised when download fails."""


class YTDLPDownloader:
    """Handles YouTube search and download using yt-dlp."""
    
    def __init__(
        self,
        config: AppConfig,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.config = config
        self.progress_callback = progress_callback
        self.ffmpeg_path = self._get_ffmpeg_path()
        
        # Ensure directories exist
        config.ensure_directories()
    
    def _get_ffmpeg_path(self) -> str:
        """Get ffmpeg executable path."""
        try:
            # Try imageio-ffmpeg first (bundled binary)
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            # Fallback to system ffmpeg
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                logger.warning("ffmpeg not found - downloads may fail")
                return "ffmpeg"  # Let yt-dlp try to find it
            return ffmpeg_path
    
    def _log(self, message: str) -> None:
        """Log message via callback or logger."""
        logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Create safe filename from input string."""
        # Use yt-dlp's sanitizer first
        safe = sanitize_filename(filename, restricted=True)
        
        # Additional cleanup for nested directories and problematic chars
        safe = re.sub(r"[\\/:*?\"<>|\n\r\t]+", "_", safe)
        safe = safe.strip("_ .")
        
        # Ensure not empty
        return safe if safe else "audio"
    
    def search_track(self, track: TrackItem) -> Optional[SearchResult]:
        """Search for a track on YouTube."""
        track.status = TrackStatus.SEARCHING
        self._log(f"[search] {track.query}")
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "default_search": "ytsearch1",
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{track.query}", download=False)
                
                if not info or "entries" not in info or not info["entries"]:
                    logger.warning(f"No search results for: {track.query}")
                    return None
                
                entry = info["entries"][0]
                
                return SearchResult(
                    title=entry.get("title", "Unknown"),
                    url=entry.get("webpage_url", ""),
                    duration=entry.get("duration"),
                    uploader=entry.get("uploader"),
                    view_count=entry.get("view_count"),
                    like_count=entry.get("like_count"),
                    upload_date=entry.get("upload_date"),
                )
                
        except Exception as e:
            logger.error(f"Search failed for {track.query}: {e}")
            return None
    
    def download_track(
        self, 
        track: TrackItem, 
        dry_run: bool = False
    ) -> DownloadResult:
        """Download a track from YouTube."""
        
        # Search first if no URL
        if not track.url:
            search_result = self.search_track(track)
            if not search_result:
                error_msg = f"No search results for: {track.query}"
                track.status = TrackStatus.ERROR
                track.error = error_msg
                return DownloadResult(success=False, error_message=error_msg)
            
            track.url = search_result.url
            track.status = TrackStatus.FOUND
            
            if dry_run:
                self._log(f"[dry-run] Found: {track.display_name}")
                return DownloadResult(success=True)
        
        if dry_run:
            return DownloadResult(success=True)
        
        # Proceed with download
        track.status = TrackStatus.DOWNLOADING
        
        # Generate output filename
        base_name = f"{track.artist} - {track.title}".strip(" -")
        if not base_name:
            base_name = track.title or track.artist or "audio"
        
        safe_filename = self._sanitize_filename(base_name)
        output_template = str(self.config.music_dir / f"{safe_filename}.%(ext)s")
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "noplaylist": True,
            "format": self.config.audio_format,
            "ffmpeg_location": self.ffmpeg_path,
            "outtmpl": {"default": output_template},
            "overwrites": self.config.overwrite_files,
            "ignoreerrors": False,
            "writeinfojson": self.config.write_info_json,
            "writethumbnail": self.config.write_thumbnail,
            
            # Audio post-processing
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "best",
                    "preferredquality": "0",  # Best available
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
        }
        
        # Add user agent if configured
        if self.config.user_agent:
            ydl_opts["http_headers"] = {"User-Agent": self.config.user_agent}
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                self._log(f"[download] {track.display_name}")
                
                # Download the track
                info = ydl.extract_info(track.url, download=True)
                
                if not info:
                    raise DownloadError("No video information retrieved")
                
                # Find the downloaded file
                downloaded_files = list(self.config.music_dir.glob(f"{safe_filename}.*"))
                
                if not downloaded_files:
                    raise DownloadError("Downloaded file not found")
                
                result_path = downloaded_files[0]
                track.result_path = str(result_path)
                track.status = TrackStatus.DONE
                track.duration = info.get("duration")
                track.filesize = result_path.stat().st_size if result_path.exists() else None
                
                self._log(f"[success] Downloaded: {result_path.name}")
                
                return DownloadResult(
                    success=True,
                    file_path=result_path,
                    duration=info.get("duration"),
                    filesize=track.filesize,
                    format_info={
                        "ext": info.get("ext", ""),
                        "acodec": info.get("acodec", ""),
                        "abr": str(info.get("abr", "")),
                    },
                )
                
        except Exception as e:
            error_msg = f"Download failed: {e}"
            track.status = TrackStatus.ERROR
            track.error = error_msg
            self._log(f"[error] {track.display_name}: {error_msg}")
            
            return DownloadResult(success=False, error_message=error_msg)
    
    def download_multiple(
        self,
        tracks: List[TrackItem],
        dry_run: bool = False,
        progress_callback: Optional[Callable[[int, int, TrackItem], None]] = None,
    ) -> List[DownloadResult]:
        """Download multiple tracks sequentially."""
        
        results: List[DownloadResult] = []
        
        for i, track in enumerate(tracks):
            # Check for cancellation point here if needed
            
            result = self.download_track(track, dry_run=dry_run)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(tracks), track)
        
        return results
    
    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information without downloading."""
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            logger.error(f"Failed to get video info for {url}: {e}")
            return None
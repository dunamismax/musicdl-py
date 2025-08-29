"""Base screen with common functionality for all download screens."""

from __future__ import annotations

import logging
import threading

from textual.screen import Screen

from ..core import TrackItem, YTDLPDownloader
from ..core.models import AppConfig, TrackStatus
from ..utils.logging import TUILogHandler, add_tui_handler, remove_tui_handler
from .components import LogPanel, ProgressDisplay, StatusDisplay

logger = logging.getLogger(__name__)


class BaseDownloadScreen(Screen):
    """Base screen with common download functionality."""

    def __init__(self, config: AppConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.downloader: YTDLPDownloader | None = None
        self.track_items: list[TrackItem] = []
        self.worker_thread: threading.Thread | None = None
        self.tui_log_handler: TUILogHandler | None = None
        self.is_running = False

        # UI components (to be set by subclasses in compose)
        self.log_panel: LogPanel | None = None
        self.progress_display: ProgressDisplay | None = None
        self.status_display: StatusDisplay | None = None

    def on_mount(self) -> None:
        """Initialize common functionality."""
        logger.info(f"{self.__class__.__name__} started")

        # Set up TUI logging
        self.tui_log_handler = add_tui_handler(self._log_to_ui, level=logging.INFO)

        # Initialize downloader
        self.downloader = YTDLPDownloader(
            config=self.config, progress_callback=self._log_to_ui
        )

        self._on_mount_custom()

    def on_unmount(self) -> None:
        """Clean up common functionality."""
        if self.tui_log_handler:
            remove_tui_handler(self.tui_log_handler)

        if self.is_running:
            self._stop_downloads()

        self._on_unmount_custom()

    def _on_mount_custom(self) -> None:
        """Custom mount logic for subclasses."""
        pass

    def _on_unmount_custom(self) -> None:
        """Custom unmount logic for subclasses (optional)."""
        pass

    def _start_downloads(self, tracks: list[TrackItem], dry_run: bool = False) -> None:
        """Start downloading tracks."""
        if self.is_running:
            self._log_to_ui("Downloads already running")
            return

        if not tracks:
            self._log_to_ui("No tracks to download")
            self._update_status("No tracks found", "warning")
            return

        self.track_items = tracks
        self.is_running = True

        # Update UI state
        self._update_download_ui(True)

        total_tracks = len(self.track_items)
        mode = "Searching" if dry_run else "Downloading"
        self._update_status(f"{mode} 0/{total_tracks} tracks", "info")
        self.progress_display.set_progress(0.0, f"0/{total_tracks}")

        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self._download_worker, args=(dry_run,), daemon=True
        )
        self.worker_thread.start()

    def _stop_downloads(self) -> None:
        """Stop the download process."""
        if not self.is_running:
            return

        self.is_running = False
        self._log_to_ui("Stopping downloads after current track...")
        self._update_status("Stopping...", "warning")

    def _download_worker(self, dry_run: bool = False) -> None:
        """Background worker for downloads."""
        if not self.downloader:
            return

        # Choose download method based on configuration
        if self.config.max_concurrent_downloads > 1 and len(self.track_items) > 1:
            self._download_concurrent(dry_run)
        else:
            self._download_sequential(dry_run)

        # Finish up
        self.call_from_thread(self._download_complete, dry_run)

    def _download_sequential(self, dry_run: bool = False) -> None:
        """Sequential download processing."""
        completed = 0
        total = len(self.track_items)

        for item in self.track_items:
            if not self.is_running:
                break

            # Update progress
            self.call_from_thread(
                self._update_progress,
                completed,
                total,
                f"Processing: {item.display_name}",
            )

            # Process track
            self._process_single_track(item, dry_run)
            completed += 1

    def _download_concurrent(self, dry_run: bool = False) -> None:
        """Concurrent download processing."""

        def progress_callback(completed: int, total: int, track: TrackItem) -> None:
            """Progress callback for concurrent downloads."""
            if not self.is_running:
                return
            # Progress update
            self.call_from_thread(
                self._update_progress,
                completed,
                total,
                f"Processing: {track.display_name}",
            )

        try:
            # Use concurrent download method
            results = self.downloader.download_multiple_concurrent(
                self.track_items,
                dry_run=dry_run,
                progress_callback=progress_callback,
                max_workers=self.config.max_concurrent_downloads,
            )

            # Log results
            for track, result in zip(self.track_items, results, strict=False):
                if not self.is_running:
                    break
                self._log_track_result(track, result, dry_run)

        except Exception as e:
            logger.error(f"Concurrent download error: {e}")
            self.call_from_thread(self._log_to_ui, f"Concurrent download failed: {e}")

    def _process_single_track(self, item: TrackItem, dry_run: bool) -> None:
        """Process a single track and log the result."""
        try:
            result = self.downloader.download_track(item, dry_run=dry_run)
            self._log_track_result(item, result, dry_run)

        except Exception as e:
            logger.error(f"Unexpected error processing {item.display_name}: {e}")
            item.status = TrackStatus.ERROR
            item.error = str(e)
            self.call_from_thread(self._log_to_ui, f"Error: {item.display_name} - {e}")

    def _log_track_result(self, track: TrackItem, result, dry_run: bool) -> None:
        """Log the result of processing a track."""
        if result.success:
            if dry_run:
                self.call_from_thread(self._log_to_ui, f"Found: {track.display_name}")
            else:
                self.call_from_thread(
                    self._log_to_ui, f"Downloaded: {track.display_name}"
                )
                if result.file_path:
                    self.call_from_thread(
                        self._log_to_ui, f"Saved to: {result.file_path}"
                    )
        else:
            self.call_from_thread(
                self._log_to_ui,
                f"Failed: {track.display_name} - {result.error_message}",
            )

    def _download_complete(self, dry_run: bool = False) -> None:
        """Handle download completion."""
        self.is_running = False

        # Update UI state
        self._update_download_ui(False)

        # Calculate results
        success_statuses = [TrackStatus.DONE, TrackStatus.FOUND]
        success_count = sum(
            1 for item in self.track_items if item.status in success_statuses
        )
        error_count = sum(
            1 for item in self.track_items if item.status == TrackStatus.ERROR
        )

        mode = "Search" if dry_run else "Download"
        self._log_to_ui(
            f"{mode} complete - Success: {success_count}, Errors: {error_count}"
        )

        if error_count == 0:
            self._update_status(
                f"Complete - {success_count} tracks processed", "success"
            )
        else:
            self._update_status(
                f"Complete - {success_count} success, {error_count} errors", "warning"
            )

        self.progress_display.complete(f"{success_count}/{len(self.track_items)}")

        # Enable export if there are results
        self._enable_export(len(self.track_items) > 0)

    def _update_progress(self, completed: int, total: int, status: str) -> None:
        """Update progress display."""
        progress = completed / max(1, total)
        self.progress_display.set_progress(progress, f"{completed}/{total}")
        self._update_status(status, "info")

    def _update_status(self, text: str, status_type: str = "info") -> None:
        """Update status display."""
        if self.status_display:
            self.status_display.set_status(text, status_type)

    def _log_to_ui(self, message: str) -> None:
        """Log message to UI panel."""
        if self.log_panel:
            self.log_panel.log_info(message)

    def _update_download_ui(self, is_downloading: bool) -> None:
        """Update UI elements when download state changes."""
        # Subclasses should override this
        pass

    def _enable_export(self, enabled: bool) -> None:
        """Enable/disable export functionality."""
        # Subclasses should override this
        pass

    def action_back_to_menu(self) -> None:
        """Go back to main menu."""
        if self.is_running:
            self._log_to_ui("Please stop downloads first")
            return

        self.app.pop_screen()

    def export_results(self, filename: str = "download_results.json") -> None:
        """Export download results to JSON file."""
        if not self.track_items:
            self._log_to_ui("No results to export")
            return

        try:
            import json
            from pathlib import Path

            output_file = Path(filename)
            results = [item.to_dict() for item in self.track_items]

            output_file.write_text(
                json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            self._log_to_ui(f"Results exported to {output_file}")
            self._update_status("Results exported", "success")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            self._log_to_ui(f"Export failed: {e}")
            self._update_status("Export failed", "error")

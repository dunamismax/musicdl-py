"""URL download application screens."""

from __future__ import annotations

import logging
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
)

from ..core import TrackItem
from ..core.models import AppConfig
from ..core.url_processor import URLParsingError, URLProcessor
from .base_screen import BaseDownloadScreen
from .components import LogPanel, ProgressDisplay, StatusDisplay

logger = logging.getLogger(__name__)


class URLDownloadScreen(BaseDownloadScreen):
    """Screen for downloading from single YouTube URLs."""

    CSS = """
    URLDownloadScreen {
        background: $surface;
    }

    #main-content {
        padding: 1;
    }

    #input-section {
        height: 8;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
    }

    #url-input {
        margin: 1 0;
    }

    #title-input {
        margin: 1 0;
    }

    #controls {
        height: 3;
        align: center middle;
        margin: 1 0;
    }

    #controls Button {
        margin: 0 1;
    }

    #info-section {
        height: 15;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
    }

    #log-panel {
        height: 10;
    }

    #progress-section {
        height: 4;
        border: solid $border;
        padding: 1;
    }

    .section-label {
        text-style: bold;
        color: $primary;
    }

    .input-label {
        color: $text;
        width: 15;
    }
    """

    BINDINGS = [
        ("ctrl+q", "app.quit", "Quit"),
        ("escape", "back_to_menu", "Back to Menu"),
    ]

    def __init__(self, config: AppConfig, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.url_processor = URLProcessor()
        self.track_item: TrackItem | None = None

    def compose(self) -> ComposeResult:
        """Compose the URL download screen."""
        yield Header(show_clock=self.config.show_clock)

        with Vertical(id="main-content"):
            # Input section
            with Vertical(id="input-section"):
                yield Label("Download from YouTube URL", classes="section-label")

                with Horizontal():
                    yield Label("URL:", classes="input-label")
                    yield Input(
                        placeholder="Enter YouTube URL (video or playlist)",
                        id="url-input",
                    )

                with Horizontal():
                    yield Label("Title (optional):", classes="input-label")
                    yield Input(
                        placeholder="Override title (leave empty to auto-detect)",
                        id="title-input",
                    )

            # Controls
            with Horizontal(id="controls"):
                yield Button("Validate URL", id="validate-btn", variant="primary")
                yield Button(
                    "Download", id="download-btn", variant="success", disabled=True
                )
                yield Button("Stop", id="stop-btn", variant="warning", disabled=True)
                yield Button("Back to Menu", id="back-btn", variant="default")

            # Info and log section
            with Vertical(id="info-section"):
                yield Label("Information & Log", classes="section-label")
                self.log_panel = LogPanel(id="log-panel")
                yield self.log_panel

            # Progress section
            with Horizontal(id="progress-section"):
                self.progress_display = ProgressDisplay(id="progress-display")
                yield self.progress_display

                self.status_display = StatusDisplay(id="status-display")
                yield self.status_display

        yield Footer()

    def _on_mount_custom(self) -> None:
        """Custom mount logic."""
        self._log_to_ui("Enter a YouTube URL to get started")
        self._update_status("Ready", "info")

    @on(Button.Pressed, "#validate-btn")
    def on_validate_pressed(self) -> None:
        """Handle validate button press."""
        self.action_validate_url()

    @on(Button.Pressed, "#download-btn")
    def on_download_pressed(self) -> None:
        """Handle download button press."""
        self.action_start_download()

    @on(Button.Pressed, "#stop-btn")
    def on_stop_pressed(self) -> None:
        """Handle stop button press."""
        self.action_stop_download()

    @on(Button.Pressed, "#back-btn")
    def on_back_pressed(self) -> None:
        """Handle back button press."""
        self.action_back_to_menu()

    def action_validate_url(self) -> None:
        """Validate the entered YouTube URL."""
        url_input = self.query_one("#url-input", Input)
        url = url_input.value.strip()

        if not url:
            self._log_to_ui("Please enter a YouTube URL")
            self._update_status("No URL provided", "warning")
            return

        if not self.url_processor.is_valid_youtube_url(url):
            self._log_to_ui("Invalid YouTube URL format")
            self._update_status("Invalid URL", "error")
            self.query_one("#download-btn", Button).disabled = True
            return

        # Check if it's a playlist
        if self.url_processor.is_playlist_url(url):
            playlist_id = self.url_processor.extract_playlist_id(url)
            self._log_to_ui("Valid YouTube playlist URL detected")
            self._log_to_ui(f"Playlist ID: {playlist_id}")
            self._log_to_ui(
                "Warning: Playlist download will get all videos in the playlist"
            )
        else:
            video_id = self.url_processor.extract_video_id(url)
            self._log_to_ui("Valid YouTube video URL detected")
            self._log_to_ui(f"Video ID: {video_id}")

        normalized_url = self.url_processor.normalize_youtube_url(url)
        self._log_to_ui(f"Normalized URL: {normalized_url}")

        self._update_status("URL validated", "success")
        self.query_one("#download-btn", Button).disabled = False

    def action_start_download(self) -> None:
        """Start downloading from the URL."""
        url_input = self.query_one("#url-input", Input)
        title_input = self.query_one("#title-input", Input)

        url = url_input.value.strip()
        title_override = title_input.value.strip() or None

        if not url or not self.url_processor.is_valid_youtube_url(url):
            self._log_to_ui("Please validate the URL first")
            return

        # Create track item
        self.track_item = self.url_processor.create_track_from_url(url, title_override)
        if not self.track_item:
            self._log_to_ui("Failed to create track from URL")
            self._update_status("Track creation failed", "error")
            return

        # Use base class method to start downloads
        self._start_downloads([self.track_item], dry_run=False)

    def action_stop_download(self) -> None:
        """Stop the current download."""
        self._stop_downloads()

    def _update_download_ui(self, is_downloading: bool) -> None:
        """Update UI elements when download state changes."""
        self.query_one("#download-btn", Button).disabled = is_downloading
        self.query_one("#stop-btn", Button).disabled = not is_downloading
        self.query_one("#validate-btn", Button).disabled = is_downloading

    def _enable_export(self, enabled: bool) -> None:
        """Enable/disable export functionality."""
        # URL download screen doesn't have export button
        pass


class TextFileDownloadScreen(BaseDownloadScreen):
    """Screen for downloading from text files containing YouTube URLs."""

    CSS = """
    TextFileDownloadScreen {
        background: $surface;
    }

    #main-content {
        padding: 1;
    }

    #input-section {
        height: 6;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
    }

    #file-input {
        margin: 1 0;
    }

    #controls {
        height: 3;
        align: center middle;
        margin: 1 0;
    }

    #controls Button {
        margin: 0 1;
    }

    #info-section {
        height: 15;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
    }

    #log-panel {
        height: 12;
    }

    #progress-section {
        height: 4;
        border: solid $border;
        padding: 1;
    }

    .section-label {
        text-style: bold;
        color: $primary;
    }

    .input-label {
        color: $text;
        width: 15;
    }
    """

    BINDINGS = [
        ("ctrl+q", "app.quit", "Quit"),
        ("escape", "back_to_menu", "Back to Menu"),
    ]

    def __init__(self, config: AppConfig, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.url_processor = URLProcessor()

    def compose(self) -> ComposeResult:
        """Compose the text file download screen."""
        yield Header(show_clock=self.config.show_clock)

        with Vertical(id="main-content"):
            # Input section
            with Vertical(id="input-section"):
                yield Label("Download from Text File URLs", classes="section-label")

                with Horizontal():
                    yield Label("Text File:", classes="input-label")
                    yield Input(
                        placeholder="Enter path to text file with YouTube URLs",
                        id="file-input",
                    )

                yield Label("Format: One YouTube URL per line", classes="help-text")

            # Controls
            with Horizontal(id="controls"):
                yield Button("Validate File", id="validate-btn", variant="primary")
                yield Button(
                    "Download All", id="download-btn", variant="success", disabled=True
                )
                yield Button("Stop", id="stop-btn", variant="warning", disabled=True)
                yield Button(
                    "Export Results", id="export-btn", variant="default", disabled=True
                )
                yield Button("Back to Menu", id="back-btn", variant="default")

            # Info and log section
            with Vertical(id="info-section"):
                yield Label("File Analysis & Log", classes="section-label")
                self.log_panel = LogPanel(id="log-panel")
                yield self.log_panel

            # Progress section
            with Horizontal(id="progress-section"):
                self.progress_display = ProgressDisplay(id="progress-display")
                yield self.progress_display

                self.status_display = StatusDisplay(id="status-display")
                yield self.status_display

        yield Footer()

    def _on_mount_custom(self) -> None:
        """Custom mount logic."""
        self._log_to_ui("Enter path to a text file containing YouTube URLs")
        self._log_to_ui(
            "Format: One URL per line (empty lines and # comments are ignored)"
        )
        self._update_status("Ready", "info")

    @on(Button.Pressed, "#validate-btn")
    def on_validate_pressed(self) -> None:
        """Handle validate button press."""
        self.action_validate_file()

    @on(Button.Pressed, "#download-btn")
    def on_download_pressed(self) -> None:
        """Handle download button press."""
        self.action_start_downloads()

    @on(Button.Pressed, "#stop-btn")
    def on_stop_pressed(self) -> None:
        """Handle stop button press."""
        self.action_stop_downloads()

    @on(Button.Pressed, "#export-btn")
    def on_export_pressed(self) -> None:
        """Handle export button press."""
        self.action_export_results()

    @on(Button.Pressed, "#back-btn")
    def on_back_pressed(self) -> None:
        """Handle back button press."""
        self.action_back_to_menu()

    def action_validate_file(self) -> None:
        """Validate the text file."""
        file_input = self.query_one("#file-input", Input)
        file_path_str = file_input.value.strip()

        if not file_path_str:
            self._log_to_ui("Please enter a text file path")
            self._update_status("No file path provided", "warning")
            return

        file_path = Path(file_path_str).expanduser().resolve()

        if not file_path.exists():
            self._log_to_ui(f"File not found: {file_path}")
            self._update_status("File not found", "error")
            self.query_one("#download-btn", Button).disabled = True
            return

        if not file_path.is_file():
            self._log_to_ui(f"Path is not a file: {file_path}")
            self._update_status("Invalid file path", "error")
            self.query_one("#download-btn", Button).disabled = True
            return

        # Validate file contents
        try:
            valid_urls, total_lines, errors = self.url_processor.validate_text_file(
                file_path
            )

            self._log_to_ui("File validation complete:")
            self._log_to_ui(f"   Total lines: {total_lines}")
            self._log_to_ui(f"   Valid URLs: {valid_urls}")
            self._log_to_ui(f"   Errors: {len(errors)}")

            if errors and len(errors) <= 10:  # Show first 10 errors
                self._log_to_ui("Errors found:")
                for error in errors[:10]:
                    self._log_to_ui(f"   • {error}")
                if len(errors) > 10:
                    self._log_to_ui(f"   ... and {len(errors) - 10} more errors")

            if valid_urls > 0:
                self._update_status(
                    f"File validated - {valid_urls} valid URLs", "success"
                )
                self.query_one("#download-btn", Button).disabled = False
            else:
                self._update_status("No valid URLs found", "warning")
                self.query_one("#download-btn", Button).disabled = True

        except URLParsingError as e:
            self._log_to_ui(f"Validation failed: {e}")
            self._update_status("Validation failed", "error")
            self.query_one("#download-btn", Button).disabled = True

    def action_start_downloads(self) -> None:
        """Start downloading from the text file."""
        file_input = self.query_one("#file-input", Input)
        file_path_str = file_input.value.strip()

        if not file_path_str:
            self._log_to_ui("Please validate the file first")
            return

        file_path = Path(file_path_str).expanduser().resolve()

        # Load tracks from file
        try:
            tracks = self.url_processor.load_urls_from_text_file(file_path)
        except URLParsingError as e:
            self._log_to_ui(f"Failed to load URLs: {e}")
            self._update_status("Failed to load URLs", "error")
            return

        if not tracks:
            self._log_to_ui("No tracks to download")
            return

        # Use base class method to start downloads
        self._start_downloads(tracks, dry_run=False)

    def action_stop_downloads(self) -> None:
        """Stop the downloads."""
        self._stop_downloads()

    def action_export_results(self) -> None:
        """Export download results."""
        self.export_results("text_download_results.json")

    def _update_download_ui(self, is_downloading: bool) -> None:
        """Update UI elements when download state changes."""
        self.query_one("#download-btn", Button).disabled = is_downloading
        self.query_one("#stop-btn", Button).disabled = not is_downloading
        self.query_one("#validate-btn", Button).disabled = is_downloading
        self.query_one("#export-btn", Button).disabled = is_downloading

    def _enable_export(self, enabled: bool) -> None:
        """Enable/disable export functionality."""
        self.query_one("#export-btn", Button).disabled = not enabled

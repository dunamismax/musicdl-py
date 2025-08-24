"""Main TUI application for MusicDL."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import List, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Switch,
)

from ..config import ConfigManager
from ..core import CSVDetection, CSVParser, TrackItem, YTDLPDownloader
from ..core.models import AppConfig, TrackStatus
from ..utils.logging import TUILogHandler, add_tui_handler, remove_tui_handler
from .components import HelpPanel, LogPanel, ProgressDisplay, StatusDisplay
from .styles import APP_CSS

logger = logging.getLogger(__name__)


class MusicDownloaderApp(App[None]):
    """Main TUI application for downloading YouTube audio from CSV."""

    CSS = APP_CSS

    BINDINGS = [
        Binding("ctrl+o", "focus_path", "Open CSV", priority=True),
        Binding("ctrl+s", "scan_csv", "Scan", priority=True),
        Binding("ctrl+r", "start_downloads", "Start", priority=True),
        Binding("ctrl+c", "stop_downloads", "Stop", priority=True),
        Binding("ctrl+d", "toggle_dry_run", "Dry Run", priority=True),
        Binding("ctrl+e", "export_results", "Export", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    # Reactive state
    csv_path = reactive("", layout=False)
    dry_run_mode = reactive(False, layout=False)
    is_running = reactive(False, layout=False)
    current_status = reactive("Ready", layout=False)

    def __init__(self, config_path: Optional[Path] = None, **kwargs) -> None:
        super().__init__(**kwargs)

        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load()

        # Initialize components
        self.csv_parser = CSVParser()
        self.downloader: Optional[YTDLPDownloader] = None

        # State
        self.csv_detection: Optional[CSVDetection] = None
        self.track_items: List[TrackItem] = []
        self.worker_thread: Optional[threading.Thread] = None
        self.tui_log_handler: Optional[TUILogHandler] = None

        # UI components (will be set in compose)
        self.csv_table: Optional[DataTable] = None
        self.progress_display: Optional[ProgressDisplay] = None
        self.status_display: Optional[StatusDisplay] = None
        self.log_panel: Optional[LogPanel] = None

    def compose(self) -> ComposeResult:
        """Compose the application layout."""

        yield Header(show_clock=self.config.show_clock, id="header")

        with Vertical(id="main-content"):
            # Top bar with CSV input and main controls
            with Horizontal(id="topbar"):
                yield Label("CSV Path:", classes="input-label")
                yield Input(
                    placeholder="Enter CSV file path or drag & drop", id="csv-input"
                )
                yield Button("Scan", id="scan-btn", variant="primary")
                yield Label("Dry Run:", classes="input-label")
                yield Switch(id="dry-run-switch")
                yield Button("Start", id="start-btn", variant="success")
                yield Button("Stop", id="stop-btn", variant="warning", disabled=True)

            # Control bar with column selection
            with Horizontal(id="controls"):
                yield Label("Artist:", classes="control-label")
                yield Select(
                    prompt="Auto Detect",
                    id="artist-select",
                    classes="column-select",
                )
                yield Label("Track:", classes="control-label")
                yield Select(
                    prompt="Auto Detect", id="track-select", classes="column-select"
                )
                yield Button("Reload", id="reload-btn")
                yield Button("Export", id="export-btn", disabled=True)

            # Main body with table and info panels
            with Horizontal(id="body"):
                # Left panel - CSV preview
                with Vertical(id="left-panel"):
                    yield Label("CSV Preview", classes="section-header")
                    self.csv_table = DataTable(
                        cursor_type="row", zebra_stripes=True, id="csv-table"
                    )
                    yield self.csv_table

                # Right panel - Help and logs
                with Vertical(id="right-panel"):
                    yield HelpPanel(id="help-panel")

                    yield Label("Application Log", classes="section-header")
                    self.log_panel = LogPanel(id="log-panel")
                    yield self.log_panel

            # Progress and status bar
            with Horizontal(id="progress-section"):
                self.progress_display = ProgressDisplay(id="progress-bar")
                yield self.progress_display

                self.status_display = StatusDisplay(id="status-display")
                yield self.status_display

        yield Footer(id="footer")

    def on_mount(self) -> None:
        """Application startup."""
        logger.info("MusicDL started")

        # Set up TUI logging
        self.tui_log_handler = add_tui_handler(self._log_to_ui, level=logging.INFO)

        # Initialize downloader
        self.downloader = YTDLPDownloader(
            config=self.config, progress_callback=self._log_to_ui
        )

        self._log_to_ui("MusicDL started - Load a CSV file to begin")
        self._update_status("Ready", "info")

    def on_unmount(self) -> None:
        """Application shutdown."""
        # Clean up logging handler
        if self.tui_log_handler:
            remove_tui_handler(self.tui_log_handler)

        # Stop any running downloads
        if self.is_running:
            self._stop_downloads()

        logger.info("MusicDL shutdown")

    # Event handlers

    @on(Input.Changed, "#csv-input")
    def on_csv_input_changed(self, event: Input.Changed) -> None:
        """Handle CSV input changes."""
        self.csv_path = event.value.strip()

    @on(Switch.Changed, "#dry-run-switch")
    def on_dry_run_changed(self, event: Switch.Changed) -> None:
        """Handle dry run toggle."""
        self.dry_run_mode = event.value
        mode_text = "DRY RUN" if self.dry_run_mode else "DOWNLOAD"
        self._update_status(f"Mode: {mode_text}", "info")

    @on(Button.Pressed, "#scan-btn")
    def on_scan_button_pressed(self) -> None:
        """Handle scan button press."""
        self.action_scan_csv()

    @on(Button.Pressed, "#reload-btn")
    def on_reload_button_pressed(self) -> None:
        """Handle reload button press."""
        self._reload_csv()

    @on(Button.Pressed, "#start-btn")
    def on_start_button_pressed(self) -> None:
        """Handle start button press."""
        self.action_start_downloads()

    @on(Button.Pressed, "#stop-btn")
    def on_stop_button_pressed(self) -> None:
        """Handle stop button press."""
        self.action_stop_downloads()

    @on(Button.Pressed, "#export-btn")
    def on_export_button_pressed(self) -> None:
        """Handle export button press."""
        self.action_export_results()

    # Actions

    def action_focus_path(self) -> None:
        """Focus the CSV path input."""
        self.query_one("#csv-input", Input).focus()

    def action_scan_csv(self) -> None:
        """Scan the CSV file."""
        if not self.csv_path:
            csv_input = self.query_one("#csv-input", Input)
            self.csv_path = csv_input.value.strip()

        if not self.csv_path:
            self._log_to_ui("Please enter a CSV file path")
            self._update_status("No CSV path provided", "warning")
            return

        csv_file = Path(self.csv_path).expanduser().resolve()
        if not csv_file.exists():
            self._log_to_ui(f"CSV file not found: {csv_file}")
            self._update_status("CSV file not found", "error")
            return

        try:
            self._update_status("Scanning CSV...", "info")
            self.csv_detection = self.csv_parser.load_csv(csv_file)
            self._populate_csv_table()
            self._populate_column_selects()

            mode = (
                "Artist/Track columns detected"
                if not self.csv_detection.single_title_col
                else f"Single column: {self.csv_detection.single_title_col}"
            )

            self._log_to_ui(
                f"Scanned {csv_file.name}: {mode} | "
                f"{len(self.csv_detection.preview_rows)} rows"
            )
            self._update_status(
                f"CSV loaded - {len(self.csv_detection.preview_rows)} rows", "success"
            )

        except Exception as e:
            logger.error(f"CSV scan failed: {e}")
            self._log_to_ui(f"Failed to scan CSV: {e}")
            self._update_status("CSV scan failed", "error")

    def action_start_downloads(self) -> None:
        """Start the download process."""
        if self.is_running:
            self._log_to_ui("Downloads already running")
            return

        if not self.csv_detection:
            self._log_to_ui("Please scan a CSV file first")
            self._update_status("No CSV loaded", "warning")
            return

        self._start_downloads()

    def action_stop_downloads(self) -> None:
        """Stop the download process."""
        if not self.is_running:
            return

        self._stop_downloads()

    def action_toggle_dry_run(self) -> None:
        """Toggle dry run mode."""
        switch = self.query_one("#dry-run-switch", Switch)
        switch.value = not switch.value

    def action_export_results(self) -> None:
        """Export download results."""
        if not self.track_items:
            self._log_to_ui("No results to export")
            return

        try:
            output_file = Path("download_results.json")
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

    # Private methods

    def _populate_csv_table(self) -> None:
        """Populate the CSV preview table."""
        if not self.csv_detection or not self.csv_table:
            return

        # Clear existing data
        self.csv_table.clear()

        # Add columns
        for header in self.csv_detection.headers:
            self.csv_table.add_column(header, key=header)

        # Add preview rows (limit to avoid performance issues)
        preview_limit = min(50, len(self.csv_detection.preview_rows))
        for i, row in enumerate(self.csv_detection.preview_rows[:preview_limit]):
            row_data = [row.get(header, "") for header in self.csv_detection.headers]
            self.csv_table.add_row(*row_data, key=str(i))

    def _populate_column_selects(self) -> None:
        """Populate the column selection dropdowns."""
        if not self.csv_detection:
            return

        artist_select = self.query_one("#artist-select", Select)
        track_select = self.query_one("#track-select", Select)

        # Create options from headers
        options = [(header, header) for header in self.csv_detection.headers]

        artist_select.set_options(options)
        track_select.set_options(options)

        # Set detected defaults
        if self.csv_detection.artist_col:
            artist_select.value = self.csv_detection.artist_col

        if self.csv_detection.track_col:
            track_select.value = self.csv_detection.track_col

    def _reload_csv(self) -> None:
        """Reload CSV with current column selections."""
        if not self.csv_detection:
            self._log_to_ui("No CSV loaded")
            return

        # Re-populate table and update detection based on user selections
        self._populate_csv_table()
        self._log_to_ui("CSV reloaded with current column selection")

    def _start_downloads(self) -> None:
        """Start the download process in a background thread."""
        if not self.csv_detection or not self.downloader:
            return

        # Get column selections
        artist_select = self.query_one("#artist-select", Select)
        track_select = self.query_one("#track-select", Select)

        artist_col = (
            artist_select.value if artist_select.value != Select.BLANK else None
        )
        track_col = track_select.value if track_select.value != Select.BLANK else None

        # Build track items
        self.track_items = self.csv_parser.build_track_items(
            self.csv_detection,
            artist_col_override=artist_col,
            track_col_override=track_col,
        )

        if not self.track_items:
            self._log_to_ui("No tracks to download - check your column selection")
            self._update_status("No tracks found", "warning")
            return

        # Update UI state
        self.is_running = True
        self.query_one("#start-btn", Button).disabled = True
        self.query_one("#stop-btn", Button).disabled = False
        self.query_one("#export-btn", Button).disabled = True

        total_tracks = len(self.track_items)
        mode = "Searching" if self.dry_run_mode else "Downloading"
        self._update_status(f"{mode} 0/{total_tracks} tracks", "info")
        self.progress_display.set_progress(0.0, f"0/{total_tracks}")

        # Start worker thread
        self.worker_thread = threading.Thread(target=self._download_worker, daemon=True)
        self.worker_thread.start()

    def _stop_downloads(self) -> None:
        """Stop the download process."""
        self.is_running = False
        self._log_to_ui("Stopping downloads after current track...")
        self._update_status("Stopping...", "warning")

    def _download_worker(self) -> None:
        """Background worker for downloads."""
        if not self.downloader:
            return

        completed = 0
        total = len(self.track_items)

        for item in self.track_items:
            if not self.is_running:
                break

            # Update progress
            mode = "search" if self.dry_run_mode else "download"
            self.call_from_thread(
                self._update_progress,
                completed,
                total,
                f"Processing: {item.display_name}",
            )

            # Process track
            try:
                result = self.downloader.download_track(item, dry_run=self.dry_run_mode)
                if result.success:
                    if self.dry_run_mode:
                        self.call_from_thread(
                            self._log_to_ui, f"Found: {item.display_name}"
                        )
                    else:
                        self.call_from_thread(
                            self._log_to_ui, f"Downloaded: {item.display_name}"
                        )
                else:
                    self.call_from_thread(
                        self._log_to_ui,
                        f"Failed: {item.display_name} - {result.error_message}",
                    )

            except Exception as e:
                logger.error(f"Unexpected error processing {item.display_name}: {e}")
                item.status = TrackStatus.ERROR
                item.error = str(e)
                self.call_from_thread(
                    self._log_to_ui, f"Error: {item.display_name} - {e}"
                )

            completed += 1

        # Finish up
        self.call_from_thread(self._download_complete)

    def _download_complete(self) -> None:
        """Handle download completion."""
        self.is_running = False

        # Update UI state
        self.query_one("#start-btn", Button).disabled = False
        self.query_one("#stop-btn", Button).disabled = True
        self.query_one("#export-btn", Button).disabled = False

        # Calculate results
        success_count = sum(
            1
            for item in self.track_items
            if item.status in [TrackStatus.DONE, TrackStatus.FOUND]
        )
        error_count = sum(
            1 for item in self.track_items if item.status == TrackStatus.ERROR
        )

        mode = "Search" if self.dry_run_mode else "Download"
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

    def _update_progress(self, completed: int, total: int, status: str) -> None:
        """Update progress display."""
        progress = completed / max(1, total)
        self.progress_display.set_progress(progress, f"{completed}/{total}")
        self._update_status(status, "info")

    def _update_status(self, text: str, status_type: str = "info") -> None:
        """Update status display."""
        self.current_status = text
        if self.status_display:
            self.status_display.set_status(text, status_type)

    def _log_to_ui(self, message: str) -> None:
        """Log message to UI panel."""
        if self.log_panel:
            self.log_panel.log_info(message)


def run_app(config_path: Optional[Path] = None) -> None:
    """Run the MusicDL TUI application."""
    app = MusicDownloaderApp(config_path=config_path)
    app.run()

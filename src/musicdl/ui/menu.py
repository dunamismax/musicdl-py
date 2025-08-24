"""Main menu system for MusicDL."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Header, Label, OptionList, Select
from textual.widgets.option_list import Option

from ..core.models import AppConfig

logger = logging.getLogger(__name__)


class FormatSelectionScreen(ModalScreen[tuple[str, str]]):
    """Screen for selecting output format and bitrate."""

    CSS = """
    FormatSelectionScreen {
        align: center middle;
    }
    
    #dialog {
        grid-size: 1 8;
        grid-gutter: 1;
        grid-rows: 1 1 1 1 1 1 1 1;
        padding: 1;
        width: 60;
        height: 22;
        border: thick $background 80%;
        background: $surface;
    }
    
    #title {
        content-align: center middle;
        height: 3;
    }
    
    .section-label {
        height: 1;
        content-align: left middle;
        text-style: bold;
    }
    
    #format-select, #bitrate-select {
        height: 3;
        margin: 0 1;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
        align: center middle;
    }
    
    #buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, current_format: str = "bestaudio/best") -> None:
        super().__init__()
        self.current_format = current_format
        self.selected_format = "bestaudio/best"
        self.selected_bitrate = "best"

    def compose(self) -> ComposeResult:
        """Compose the format selection dialog."""
        with Vertical(id="dialog"):
            yield Label("Select Audio Format & Quality", id="title")

            yield Label("Format:", classes="section-label")
            yield Select(
                [
                    ("Best Available", "bestaudio/best"),
                    ("MP3", "mp3"),
                    ("AAC", "aac"),
                    ("OGG", "ogg"),
                    ("M4A", "m4a"),
                    ("FLAC", "flac"),
                    ("WAV", "wav"),
                ],
                value="bestaudio/best",
                id="format-select",
            )

            yield Label("Bitrate/Quality:", classes="section-label")
            yield Select(
                [
                    ("Best Available", "best"),
                    ("320k (High)", "320"),
                    ("256k (Good)", "256"),
                    ("192k (Standard)", "192"),
                    ("128k (Basic)", "128"),
                    ("96k (Low)", "96"),
                ],
                value="best",
                id="bitrate-select",
            )

            with Center(id="buttons"):
                yield Button("OK", variant="primary", id="ok-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        """Set initial values based on current format."""
        format_select = self.query_one("#format-select", Select)
        bitrate_select = self.query_one("#bitrate-select", Select)

        # Parse current format to set defaults
        if "/" in self.current_format:
            format_part, quality_part = self.current_format.split("/", 1)
            if format_part in ["bestaudio", "best"]:
                format_select.value = "bestaudio/best"
            else:
                format_select.value = format_part
        else:
            format_select.value = self.current_format

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "ok-btn":
            format_select = self.query_one("#format-select", Select)
            bitrate_select = self.query_one("#bitrate-select", Select)

            selected_format = format_select.value or "bestaudio/best"
            selected_bitrate = bitrate_select.value or "best"

            # Build format string
            if selected_format == "bestaudio/best":
                format_string = "bestaudio/best"
            elif selected_bitrate == "best":
                format_string = f"bestaudio[acodec={selected_format}]/best"
            else:
                format_string = (
                    f"bestaudio[acodec={selected_format}][abr<={selected_bitrate}]/best"
                )

            self.dismiss((selected_format, format_string))
        else:
            self.dismiss((self.current_format, self.current_format))


class MainMenuScreen(ModalScreen[str]):
    """Main menu screen with navigation options."""

    CSS = """
    MainMenuScreen {
        align: center middle;
        background: $surface;
    }
    
    #menu-container {
        width: 80;
        height: 20;
        border: thick $primary 80%;
        padding: 2;
    }
    
    #title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $primary;
    }
    
    #subtitle {
        height: 2;
        content-align: center middle;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #options {
        height: 10;
        border: solid $border;
    }
    
    #footer-text {
        height: 2;
        content-align: center middle;
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main menu."""
        with Vertical(id="menu-container"):
            yield Label("MusicDL", id="title")
            yield Label("YouTube Audio Downloader", id="subtitle")

            yield OptionList(
                Option("Download tracks from CSV file", id="csv"),
                Option("Download track or playlist from YouTube link", id="url"),
                Option("Download from text file of YouTube URLs", id="text"),
                Option("Settings & Format Options", id="settings"),
                Option("Exit", id="exit"),
                id="options",
            )

            yield Label("Use Up/Down arrows to navigate, Enter to select", id="footer-text")

    def on_mount(self) -> None:
        """Focus the options list when mounted."""
        self.query_one("#options", OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle menu option selection."""
        if event.option.id:
            self.dismiss(event.option.id)


class SettingsScreen(ModalScreen[Optional[AppConfig]]):
    """Settings configuration screen."""

    CSS = """
    SettingsScreen {
        align: center middle;
    }
    
    #settings-dialog {
        width: 70;
        height: 25;
        border: thick $primary 80%;
        padding: 2;
        background: $surface;
    }
    
    #settings-title {
        height: 2;
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .setting-section {
        height: 3;
        margin-bottom: 1;
    }
    
    .setting-label {
        height: 1;
        text-style: bold;
        color: $text;
    }
    
    .current-value {
        height: 1;
        color: $text-muted;
        text-style: italic;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
        align: center middle;
        margin-top: 2;
    }
    
    #buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.format_changed = False

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with Vertical(id="settings-dialog"):
            yield Label("Settings", id="settings-title")

            with Vertical(classes="setting-section"):
                yield Label("Audio Format & Quality:", classes="setting-label")
                yield Label(
                    f"Current: {self.config.audio_format}", classes="current-value"
                )
                yield Button(
                    "Change Format & Bitrate", id="format-btn", variant="primary"
                )

            with Vertical(classes="setting-section"):
                yield Label("Music Directory:", classes="setting-label")
                yield Label(
                    f"Current: {self.config.music_dir}", classes="current-value"
                )

            with Vertical(classes="setting-section"):
                yield Label("Overwrite Files:", classes="setting-label")
                yield Label(
                    f"Current: {'Yes' if self.config.overwrite_files else 'No'}",
                    classes="current-value",
                )

            with Center(id="buttons"):
                yield Button("Done", variant="primary", id="done-btn")
                yield Button("Cancel", id="cancel-btn")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "format-btn":
            result = await self.app.push_screen_wait(
                FormatSelectionScreen(self.config.audio_format)
            )
            if result and len(result) == 2:
                _, format_string = result
                if format_string != self.config.audio_format:
                    self.config.audio_format = format_string
                    self.format_changed = True
                    # Update the display
                    current_label = self.query_one(".current-value", Label)
                    current_label.update(f"Current: {format_string}")

        elif event.button.id == "done-btn":
            if self.format_changed:
                self.dismiss(self.config)
            else:
                self.dismiss(None)

        else:  # cancel
            self.dismiss(None)

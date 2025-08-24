"""Main application with menu system integration."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from textual.app import App

from ..config import ConfigManager
from .app import MusicDownloaderApp
from .menu import MainMenuScreen, SettingsScreen
from .url_app import TextFileDownloadScreen, URLDownloadScreen

logger = logging.getLogger(__name__)


class MusicDLMainApp(App[None]):
    """Main MusicDL application with menu system."""

    TITLE = "MusicDL - YouTube Audio Downloader"

    def __init__(
        self,
        config_path: Optional[Path] = None,
        csv_path: Optional[str] = None,
        dry_run: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load()

        # Store CLI arguments
        self.csv_path = csv_path
        self.dry_run = dry_run

        # If CSV path is provided, skip menu and go straight to CSV mode
        self.skip_menu = csv_path is not None

    def on_mount(self) -> None:
        """Application startup."""
        logger.info("MusicDL Main App started")

        if self.skip_menu:
            # Go directly to CSV mode - use the original app
            csv_app = MusicDownloaderApp(config_path=self.config_manager.config_path)
            if self.csv_path:
                csv_app.csv_path = self.csv_path
            if self.dry_run:
                csv_app.dry_run_mode = self.dry_run

            # Replace this app with the CSV app
            self.exit()
            csv_app.run()
        else:
            # Show main menu
            self.push_screen(MainMenuScreen(), self._handle_menu_selection)

    async def _handle_menu_selection(self, selection: str) -> None:
        """Handle main menu selection."""
        if selection == "csv":
            # CSV download mode
            csv_app = MusicDownloaderApp(config_path=self.config_manager.config_path)
            self.exit()  # Exit this app
            csv_app.run()  # Run the CSV app

        elif selection == "url":
            # Single URL download mode
            self.push_screen(URLDownloadScreen(self.config))

        elif selection == "text":
            # Text file URLs download mode
            self.push_screen(TextFileDownloadScreen(self.config))

        elif selection == "settings":
            # Settings screen
            result = await self.push_screen_wait(SettingsScreen(self.config))
            if result:
                # Config was updated
                self.config = result
                self.config_manager.save(self.config)
                logger.info("Configuration updated and saved")

            # Return to main menu
            self.push_screen(MainMenuScreen(), self._handle_menu_selection)

        elif selection == "exit":
            # Exit application
            self.exit()

        else:
            # Unknown selection, return to menu
            logger.warning(f"Unknown menu selection: {selection}")
            self.push_screen(MainMenuScreen(), self._handle_menu_selection)


def run_main_app(
    config_path: Optional[Path] = None,
    csv_path: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Run the main MusicDL application with menu system."""

    try:
        app = MusicDLMainApp(
            config_path=config_path, csv_path=csv_path, dry_run=dry_run
        )
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"Application error: {e}", file=sys.stderr)
        sys.exit(1)

"""Command-line interface for MusicDL."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from . import PROJECT_ROOT, __version__
from .config import load_config
from .ui.app import run_app
from .utils.bootstrap import ensure_uv_environment
from .utils.logging import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="musicdl",
        description="MusicDL - A modern TUI for downloading YouTube audio from CSV playlists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  musicdl                           # Start TUI
  musicdl --csv tracks.csv          # Start with CSV pre-loaded
  musicdl --config config.json     # Use custom config file
  musicdl --dry-run                 # Start in dry-run mode
  musicdl --version                 # Show version

For more information, visit: https://github.com/sawyer/musicdl-py
        """.strip(),
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    parser.add_argument(
        "--csv",
        type=Path,
        help="CSV file to load on startup",
        metavar="PATH",
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file path",
        metavar="PATH",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Start in dry-run mode (search only, no downloads)",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Skip UV environment bootstrap (for development)",
    )
    
    return parser


def bootstrap_if_needed() -> None:
    """Bootstrap UV environment if not already running in one."""
    try:
        ensure_uv_environment(
            project_root=PROJECT_ROOT,
            reexec=True,
        )
    except Exception as e:
        print(f"Bootstrap failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI application."""
    
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Bootstrap UV environment unless explicitly disabled
    if not args.no_bootstrap:
        bootstrap_if_needed()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Set up logging
    try:
        setup_logging(
            logs_dir=config.logs_dir,
            log_level=args.log_level,
        )
        logger = logging.getLogger(__name__)
        logger.info(f"MusicDL v{__version__} starting")
        
    except Exception as e:
        print(f"Failed to set up logging: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Import and run the TUI application
    try:
        from .ui.app import MusicDownloaderApp
        
        app = MusicDownloaderApp(config_path=args.config)
        
        # Apply CLI arguments
        if args.csv:
            app.csv_path = str(args.csv.resolve())
        
        if args.dry_run:
            app.dry_run_mode = True
        
        logger.info("Starting TUI application")
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"Application error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
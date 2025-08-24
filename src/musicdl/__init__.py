"""MusicDL - A modern TUI for downloading YouTube audio from CSV playlists."""

__version__ = "1.0.0"
__author__ = "Sawyer"
__email__ = "sawyer@example.com"

from pathlib import Path

# Package directories
PACKAGE_ROOT = Path(__file__).parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
]
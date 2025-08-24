# MusicDL

A modern TUI application for downloading YouTube audio with multiple input methods and interactive navigation.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![UV](https://img.shields.io/badge/dependency--manager-UV-orange.svg)

## Features

- **CSV Processing** - Smart detection of Artist/Track columns or "Artist - Title" format
- **Single URLs** - Download individual YouTube videos or playlists
- **Batch Processing** - Handle text files with multiple URLs
- **Format Selection** - Choose audio format (MP3, AAC, FLAC) and bitrate
- **Modern TUI** - Interactive menu navigation with real-time progress
- **Export Results** - JSON export of download results and errors

## Quick Start

### 1. Install UV (if not already installed)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/sawyer/musicdl-py.git
cd musicdl-py

# Create virtual environment with UV
uv venv

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### 3. Run the Application

```bash
# Run with UV (recommended - handles environment automatically)
uv run python -m musicdl

# Or if environment is activated:
python -m musicdl
```

### 4. Navigate the Menu

Use **↑/↓ arrows** to navigate and **Enter** to select:
- **CSV Mode** - Upload and process CSV files 
- **URL Mode** - Download single YouTube links
- **Text Mode** - Batch download from URL lists
- **Settings** - Configure formats and quality
- **Exit** - Close application

## Supported Input Formats

### CSV Files
```csv
# Separate columns
Artist,Title
Howard Shore,Concerning Hobbits
Hans Zimmer,He's a Pirate

# Single column
Track
Howard Shore - Concerning Hobbits
Hans Zimmer - He's a Pirate
```

### Text Files (URLs)
```
# One URL per line, comments supported
https://www.youtube.com/watch?v=abc123
https://youtu.be/def456
# This is a comment
https://www.youtube.com/playlist?list=xyz789
```

## Command Line Options

```bash
# Interactive menu (default)
uv run python -m musicdl

# Direct CSV mode
uv run python -m musicdl --csv tracks.csv

# Dry run (search only)
uv run python -m musicdl --dry-run

# Debug logging
uv run python -m musicdl --log-level DEBUG
```

## Configuration

Settings are stored in standard locations:
- **Linux/macOS**: `~/.config/musicdl/config.json`
- **Windows**: `%APPDATA%/musicdl/config.json`

Configure via the Settings menu or edit the JSON file directly.

## Development

```bash
# Setup development environment
git clone https://github.com/sawyer/musicdl-py.git
cd musicdl-py

# Create environment and install dev dependencies  
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Run tests and linting
pytest
ruff check src/ tests/
ruff format src/ tests/
```

## Troubleshooting

**UV Installation Issues:**
```bash
# Manual UV installation
curl -LsSf https://astral.sh/uv/install.sh | sh    # macOS/Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
```

**Download Issues:**
- Verify internet connection and URLs
- Try dry-run mode first to test searches  
- Some content may not be available due to regional restrictions

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloading
- [Textual](https://textual.textualize.io/) - Modern TUI framework  
- [UV](https://docs.astral.sh/uv/) - Fast Python package management

**Note:** For personal use only. Respect YouTube's Terms of Service and copyright laws.

# MusicDL

A modern TUI application for downloading YouTube audio with CSV processing, concurrent downloads, and high-quality Opus format output.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![UV](https://img.shields.io/badge/dependency--manager-UV-orange.svg)

## Features

- **CSV Auto-Detection** - Automatically finds and loads CSV files from project directory
- **Smart Column Detection** - Identifies Artist/Title columns or "Artist - Title" format
- **High-Quality Audio** - Opus format in WebM containers for optimal quality and compression
- **Concurrent Downloads** - Multi-threaded downloading with speed optimizations
- **Interactive TUI** - Real-time progress tracking with modern terminal interface
- **Flexible Output** - Downloads to ~/Downloads/MusicDL Downloads with YouTube video titles

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

### 4. Navigate the Interface

The application automatically detects tracks.csv in the project directory. Use:
- **Arrow keys** - Navigate menu and interface elements
- **CSV Mode** - Process CSV files with Artist/Title data
- **URL Mode** - Download individual YouTube videos
- **Settings** - Configure audio format and download options
- **Ctrl+Q** - Exit application

## Supported Input Formats

### CSV Files
```csv
# Three-column format (Title, Artist, Album)
Title,Artist,Album
Bilbo's Adventure,Howard Shore,
He's a Pirate,Klaus Badelt & Hans Zimmer,Pirates of the Caribbean

# Two-column format
Artist,Title
Howard Shore,Concerning Hobbits
Hans Zimmer,Time
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

## Output and Configuration

Audio files are downloaded to `~/Downloads/MusicDL Downloads/` using the actual YouTube video titles. Default format is Opus in WebM containers for high quality and small file size.

Settings stored at:
- **Linux/macOS**: `~/.config/musicdl/config.json`
- **Windows**: `%APPDATA%/musicdl/config.json`

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

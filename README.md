# MusicDL

A modern, fast, and user-friendly TUI application for downloading YouTube audio from CSV playlists.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![UV](https://img.shields.io/badge/dependency--manager-UV-orange.svg)

## Features

- **Smart CSV Processing** - Automatically detects Artist/Track columns or single "Artist - Title" format
- **Modern TUI Interface** - Built with Textual 5.x for a responsive terminal experience
- **High-Quality Audio** - Downloads the best available audio format using yt-dlp
- **Dry Run Mode** - Search and preview tracks without downloading
- **Progress Tracking** - Real-time progress bars and detailed logging
- **Configurable** - Customizable output directories, formats, and behavior
- **Fast Setup** - Automatic UV environment management with zero configuration

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [UV package manager](https://docs.astral.sh/uv/) (installed automatically if missing)

### Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sawyer/musicdl-py.git
   cd musicdl-py
   ```

2. **Run the application:**
   ```bash
   python -m musicdl
   ```
   
   The first run will automatically:
   - Install UV if not present
   - Create a virtual environment
   - Install all dependencies
   - Launch the TUI interface

3. **Or install as a package:**
   ```bash
   uv pip install -e .
   musicdl
   ```

## CSV Format Support

### Separate Columns
```csv
Artist,Title,Album
Howard Shore,Concerning Hobbits,LOTR Fellowship Soundtrack
Hans Zimmer,He's a Pirate,Pirates of Caribbean Soundtrack
```

### Single Column  
```csv
Track
Howard Shore - Concerning Hobbits
Hans Zimmer - He's a Pirate
```

The application automatically detects which format your CSV uses.

## Usage Examples

```bash
# Basic usage
musicdl

# Load CSV file on startup
musicdl --csv my-playlist.csv

# Start in dry-run mode
musicdl --dry-run

# Use custom configuration
musicdl --config ~/.config/musicdl/config.json

# Enable debug logging
musicdl --log-level DEBUG
```

## Key Features

### 🎵 **Intelligent CSV Processing**
- Automatic column detection using synonym matching
- Support for both separate and combined artist-title columns
- Manual column override capabilities
- Preview up to 200 rows for verification

### 🚀 **Modern Architecture** 
- Built with latest yt-dlp (2025.08.22) with YouTube compatibility
- UV package manager for 10-100x faster dependency resolution
- FFmpeg integration via imageio-ffmpeg for audio processing
- Pydantic models for robust configuration and data validation

### 🎨 **Enhanced User Interface**
- Responsive TUI built with Textual 5.x
- Real-time progress tracking and status updates  
- Comprehensive keyboard shortcuts
- Rich logging with color-coded messages
- Dark theme optimized for terminal use

### ⚙️ **Professional Configuration**
- XDG-compliant configuration directory
- JSON-based settings with validation
- Configurable output templates and directories
- Advanced yt-dlp options support

## Project Structure

```
musicdl-py/
├── src/musicdl/          # Main application code
│   ├── core/             # Core business logic  
│   ├── ui/               # TUI interface components
│   ├── utils/            # Utility functions
│   └── config.py         # Configuration management
├── tests/                # Unit tests
├── docs/                 # Documentation
├── examples/             # Example CSV files
└── pyproject.toml        # Modern Python packaging
```

## Development

### Setup Development Environment

```bash
# Clone and enter directory
git clone https://github.com/sawyer/musicdl-py.git
cd musicdl-py

# Install with development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/musicdl
```

### Code Quality

The project uses modern Python tooling:
- **Ruff** - Lightning-fast linting and formatting
- **MyPy** - Static type checking
- **Pytest** - Testing framework
- **Pre-commit** - Git hooks for code quality

## Requirements

Based on latest documentation (August 2025):

- **Python 3.10+** (3.9 reaches EOL in October 2025)
- **yt-dlp 2025.0.0+** - Latest YouTube compatibility
- **UV package manager** - Fast dependency management
- **FFmpeg** - Audio processing (auto-installed via imageio-ffmpeg)
- **Textual 5.3+** - Modern TUI framework

## Configuration

Configuration files are stored in standard locations:
- **Linux/macOS**: `~/.config/musicdl/config.json`
- **Windows**: `%APPDATA%/musicdl/config.json`

Example configuration:
```json
{
  "music_dir": "Music",
  "audio_format": "bestaudio/best", 
  "output_template": "{artist} - {title}.%(ext)s",
  "max_concurrent_downloads": 1,
  "overwrite_files": true,
  "theme": "dark"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Troubleshooting

### Common Issues

**UV Not Found Error:**
```bash
# Install UV manually
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
```

**Download Failures:**
- Check internet connection
- Verify track names in CSV
- Try dry-run mode first to test searches
- Some content may not be available

**Permission Errors:**
- Ensure write permissions to output directory
- Check disk space availability

For detailed troubleshooting, see [docs/usage.md](docs/usage.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloading capability
- [Textual](https://textual.textualize.io/) - Modern TUI framework  
- [UV](https://docs.astral.sh/uv/) - Fast Python package management
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation

---

**Note:** This tool is for personal use only. Respect YouTube's Terms of Service and copyright laws. Only download content you have the right to download.

# MusicDL Usage Guide

## Installation

### Prerequisites

MusicDL requires:
- Python 3.10 or higher
- [UV package manager](https://docs.astral.sh/uv/) for dependency management

### Installing UV

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell as Administrator):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installing MusicDL

1. Clone the repository:
```bash
git clone https://github.com/sawyer/musicdl-py.git
cd musicdl-py
```

2. Run the application (UV environment will be created automatically):
```bash
python -m musicdl
```

Or install as a package:
```bash
uv pip install -e .
musicdl
```

## CSV Format

MusicDL supports two CSV formats:

### Separate Artist and Track Columns
```csv
Artist,Title,Album
The Beatles,Hey Jude,The Beatles 1967-1970
Queen,Bohemian Rhapsody,A Night at the Opera
```

### Single Column Format
```csv
Song
The Beatles - Hey Jude
Queen - Bohemian Rhapsody  
```

The application automatically detects which format your CSV uses.

## Using the Application

### 1. Load Your CSV File

- Enter the path to your CSV file in the "CSV Path" field
- Click "Scan" to analyze the file
- The application will automatically detect Artist and Track columns

### 2. Verify Column Detection

- Check the detected columns in the dropdowns
- Manually select different columns if the detection is incorrect
- Click "Reload" to refresh the preview with your selections

### 3. Choose Download Mode

- **Download Mode**: Actually downloads audio files to the Music directory
- **Dry Run Mode**: Only searches for tracks without downloading

### 4. Start Processing

- Click "Start" to begin processing your CSV
- Use "Stop" to cancel at any time
- Monitor progress in the log panel

### 5. Export Results

- Click "Export" to save results to a JSON file
- Results include success/failure status and file paths

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Focus CSV path input |
| `Ctrl+S` | Scan CSV file |
| `Ctrl+R` | Start downloads |
| `Ctrl+C` | Stop downloads |
| `Ctrl+D` | Toggle dry run mode |
| `Ctrl+E` | Export results |
| `Ctrl+Q` | Quit application |

## Command Line Options

```bash
musicdl --help                    # Show help
musicdl --version                 # Show version
musicdl --csv tracks.csv          # Pre-load CSV file
musicdl --dry-run                 # Start in dry-run mode
musicdl --config config.json     # Use custom config
musicdl --log-level DEBUG         # Set logging level
```

## Configuration

MusicDL stores configuration in:
- **Linux/macOS**: `~/.config/musicdl/config.json`
- **Windows**: `%APPDATA%/musicdl/config.json`

### Configuration Options

```json
{
  "music_dir": "Music",
  "audio_format": "bestaudio/best",
  "max_concurrent_downloads": 1,
  "overwrite_files": true,
  "output_template": "{artist} - {title}.%(ext)s",
  "theme": "dark",
  "show_clock": true
}
```

## Output Files

Downloaded files are saved to the `Music` directory with the format:
```
Artist - Title.ext
```

Where `ext` is the best available audio format (usually `.m4a`, `.opus`, or `.webm`).

## Troubleshooting

### Common Issues

**"UV not found"**
- Install UV using the commands above
- Restart your terminal after installation

**"No search results"**
- Check your internet connection
- Verify the artist/track names in your CSV
- Some tracks may not be available on YouTube

**"Download failed"**
- YouTube may be blocking requests temporarily
- Try again later or use dry-run mode first

### Getting Help

- Check the application log panel for detailed error messages
- Use `--log-level DEBUG` for verbose logging
- Report issues at: https://github.com/sawyer/musicdl-py/issues

## Advanced Usage

### Batch Processing Multiple CSVs

```bash
for csv_file in *.csv; do
  musicdl --csv "$csv_file" --dry-run
done
```

### Custom Output Directory

Edit your configuration file to change the output directory:
```json
{
  "music_dir": "/path/to/your/music/library"
}
```
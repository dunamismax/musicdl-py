"""Reusable UI components for MusicDL."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Label, ProgressBar, Static


class StatusDisplay(Static):
    """Display current status information."""

    status_text = reactive("Ready", layout=False)
    status_type = reactive("info", layout=False)  # info, success, warning, error

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.update_display()

    def watch_status_text(self, text: str) -> None:
        """Update display when status text changes."""
        self.update_display()

    def watch_status_type(self, status_type: str) -> None:
        """Update display when status type changes."""
        self.update_display()

    def update_display(self) -> None:
        """Update the visual display."""
        css_class = f"{self.status_type}-text"
        self.update(f"[{css_class}]{self.status_text}[/{css_class}]")

    def set_status(self, text: str, status_type: str = "info") -> None:
        """Set status text and type."""
        self.status_text = text
        self.status_type = status_type


class ProgressDisplay(Static):
    """Display progress information with bar and text."""

    progress_value = reactive(0.0, layout=False)
    progress_text = reactive("", layout=False)
    show_eta = reactive(True, layout=False)

    def __init__(self, total: int = 100, **kwargs) -> None:
        super().__init__(**kwargs)
        self.total = total
        self.progress_bar: ProgressBar | None = None
        self.progress_label: Label | None = None

    def compose(self):
        """Compose the progress display."""
        from textual.containers import Horizontal

        with Horizontal(classes="status-bar"):
            self.progress_bar = ProgressBar(
                total=self.total, show_eta=self.show_eta, classes="progress-bar"
            )
            yield self.progress_bar

            self.progress_label = Label(
                self.progress_text or "0%", classes="status-label"
            )
            yield self.progress_label

    def watch_progress_value(self, value: float) -> None:
        """Update progress bar when value changes."""
        if self.progress_bar:
            self.progress_bar.progress = int(value * self.total)

    def watch_progress_text(self, text: str) -> None:
        """Update progress label when text changes."""
        if self.progress_label:
            self.progress_label.update(text)

    def set_progress(self, value: float, text: str = "") -> None:
        """Set both progress value and text."""
        self.progress_value = max(0.0, min(1.0, value))
        if text:
            self.progress_text = text
        else:
            # Generate percentage text
            percentage = int(self.progress_value * 100)
            self.progress_text = f"{percentage}%"

    def reset(self) -> None:
        """Reset progress to zero."""
        self.set_progress(0.0, "0%")

    def complete(self, text: str = "Complete") -> None:
        """Mark as complete."""
        self.set_progress(1.0, text)


class CSVPreviewTable(Static):
    """Enhanced CSV preview table."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data_table = None

    def compose(self):
        """Compose the CSV preview table."""
        from textual.widgets import DataTable

        self.data_table = DataTable(
            cursor_type="row", zebra_stripes=True, id="csv-table"
        )
        yield self.data_table

    def load_data(self, headers: list[str], rows: list[list[str]]) -> None:
        """Load CSV data into the table."""
        if not self.data_table:
            return

        # Clear existing data
        self.data_table.clear()

        # Add columns
        for header in headers:
            self.data_table.add_column(header, key=header)

        # Add rows
        for i, row in enumerate(rows):
            # Ensure row has same length as headers
            padded_row = row + [""] * (len(headers) - len(row))
            truncated_row = padded_row[: len(headers)]

            self.data_table.add_row(*truncated_row, key=str(i))

    def highlight_columns(self, columns: list[str]) -> None:
        """Highlight specific columns."""
        # This would require custom styling - placeholder for now
        pass

    def clear_data(self) -> None:
        """Clear all data from the table."""
        if self.data_table:
            self.data_table.clear()


class LogPanel(Static):
    """Enhanced log display panel."""

    max_lines = reactive(1000, layout=False)
    auto_scroll = reactive(True, layout=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.log_widget = None

    def compose(self):
        """Compose the log panel."""
        from textual.widgets import RichLog

        self.log_widget = RichLog(
            highlight=True,
            markup=True,
            wrap=True,
            auto_scroll=self.auto_scroll,
        )
        yield self.log_widget

    def write(self, message: str, markup: bool = True) -> None:
        """Write a message to the log."""
        if self.log_widget:
            if markup:
                self.log_widget.write(message)
            else:
                self.log_widget.write_line(message)

            # Limit number of lines
            if len(self.log_widget.lines) > self.max_lines:
                # Remove oldest lines
                lines_to_remove = len(self.log_widget.lines) - self.max_lines
                for _ in range(lines_to_remove):
                    self.log_widget.clear()  # This isn't ideal, but log doesn't have line removal

    def clear(self) -> None:
        """Clear all log messages."""
        if self.log_widget:
            self.log_widget.clear()

    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.write(f"[info-text]INFO[/info-text]: {message}")

    def log_success(self, message: str) -> None:
        """Log a success message."""
        self.write(f"[success-text]SUCCESS[/success-text]: {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.write(f"[warning-text]WARNING[/warning-text]: {message}")

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.write(f"[error-text]ERROR[/error-text]: {message}")


class HelpPanel(Static):
    """Help information panel."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.help_content = self._get_help_content()

    def compose(self):
        """Compose the help panel."""
        from textual.widgets import Markdown

        yield Markdown(self.help_content, id="help-panel")

    def _get_help_content(self) -> str:
        """Get the help content markdown."""
        return """
# MusicDL - YouTube Audio Downloader

## Quick Start

1. **Load CSV**: Enter path to your CSV file and click **Scan**
2. **Verify Columns**: Check detected Artist/Track columns (adjust if needed)
3. **Choose Mode**: Toggle **Dry Run** to search without downloading
4. **Start Download**: Click **Start** to begin processing

## Keyboard Shortcuts

- `Ctrl+O` - Focus CSV path input
- `Ctrl+S` - Scan CSV file
- `Ctrl+R` - Start downloads
- `Ctrl+C` - Stop downloads
- `Ctrl+D` - Toggle dry run mode
- `Ctrl+Q` - Quit application

## CSV Format

Your CSV should contain either:
- **Separate columns** for Artist and Track/Title
- **Single column** with "Artist - Title" format

## Output

Audio files are saved to the **Music** directory in the highest available quality.
        """

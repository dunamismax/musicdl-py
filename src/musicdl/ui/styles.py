"""CSS styles for the MusicDL TUI."""

APP_CSS = """
Screen {
    layout: vertical;
}

#header {
    dock: top;
    height: 3;
}

#footer {
    dock: bottom;
    height: 3;
}

#main-content {
    height: 1fr;
    layout: vertical;
}

#topbar {
    height: 3;
    background: $surface;
    padding: 0 1;
    content-align: left middle;
    border: solid $accent 10%;
}

#controls {
    height: 5;
    background: $boost;
    padding: 0 1;
    border: solid $accent 10%;
}

#body {
    height: 1fr;
    layout: horizontal;
}

#left-panel, #right-panel {
    border: solid $accent 10%;
    padding: 1;
}

#left-panel {
    width: 60%;
}

#right-panel {
    width: 40%;
}

#progress-section {
    height: 4;
    dock: bottom;
    padding: 0 1;
    background: $surface;
    border: solid $accent 10%;
}

#csv-table {
    height: 1fr;
    border: solid $accent;
}

#help-panel {
    height: 12;
    border: solid $accent;
    padding: 1;
}

#log-panel {
    height: 1fr;
    border: solid $accent;
    padding: 1;
    margin-top: 1;
}

.input-group {
    layout: horizontal;
    height: 3;
    align: left middle;
}

.input-group Label {
    width: auto;
    padding-right: 1;
    content-align: right middle;
}

.input-group Input {
    width: 1fr;
}

.input-group Select {
    width: 1fr;
}

.input-group Button {
    width: auto;
    margin-left: 1;
}

.control-row {
    layout: horizontal;
    height: 3;
    align: left middle;
    padding: 0 1;
}

.control-row Label {
    width: auto;
    padding-right: 1;
}

.control-row Select {
    width: 15;
    margin-right: 1;
}

.control-row Button {
    width: auto;
    margin-left: 1;
}

.control-row Switch {
    width: auto;
    margin-right: 1;
}

.section-header {
    background: $boost;
    color: $text;
    text-style: bold;
    padding: 0 1;
    height: 1;
}

.status-bar {
    layout: horizontal;
    height: 3;
    align: left middle;
    background: $surface;
    padding: 0 1;
}

.progress-bar {
    width: 1fr;
    margin-right: 1;
}

.status-label {
    width: auto;
    min-width: 15;
}

#dry-run-indicator {
    background: $warning;
    color: $text;
    text-style: bold;
}

#download-indicator {
    background: $success;
    color: $text; 
    text-style: bold;
}

.error-text {
    color: $error;
    text-style: bold;
}

.success-text {
    color: $success;
    text-style: bold;
}

.warning-text {
    color: $warning;
    text-style: bold;
}

.info-text {
    color: $info;
}

.highlight-row {
    background: $accent 20%;
}

Button.primary {
    background: $primary;
    color: $text;
}

Button.success {
    background: $success;
    color: $text;
}

Button.warning {
    background: $warning;
    color: $text;
}

Button.error {
    background: $error;
    color: $text;
}

Select:focus {
    border: solid $primary;
}

Input:focus {
    border: solid $primary;
}

DataTable:focus {
    border: solid $primary;
}

Log {
    scrollbar-gutter: stable;
}

ProgressBar > .bar--complete {
    color: $success;
}

ProgressBar > .bar--indeterminate {
    color: $warning;
}

Switch.-on {
    background: $success;
}

Switch.-off {
    background: $surface;
}
"""
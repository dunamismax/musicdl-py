"""CSV parsing and track detection functionality."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .models import CSVDetection, TrackItem

# Synonyms for artist column detection
ARTIST_SYNONYMS: Set[str] = {
    "artist",
    "artists", 
    "primary artist",
    "main artist",
    "lead artist",
    "performer",
    "band",
    "singer", 
    "vocalist",
    "composer",
    "author",
    "musician",
    "artist name",
    "album artist",
    "primary",
    "group",
}

# Synonyms for track column detection  
TRACK_SYNONYMS: Set[str] = {
    "track",
    "track name",
    "song",
    "song name", 
    "title",
    "recording",
    "work",
    "composition",
    "piece",
    "single",
    "name",
}

# Separators for parsing single artist-title columns
SEPARATORS: List[str] = [" - ", " — ", " – ", "-", "—", "–", ":", "|", "·"]


class CSVParsingError(Exception):
    """Raised when CSV parsing fails."""


class CSVParser:
    """Handles CSV file parsing and column detection."""
    
    def __init__(
        self,
        max_preview_rows: int = 200,
        sample_bytes: int = 64 * 1024,
    ) -> None:
        self.max_preview_rows = max_preview_rows
        self.sample_bytes = sample_bytes
    
    def sniff_csv(self, path: Path) -> Tuple[bool, csv.Dialect, str]:
        """Detect CSV format and encoding."""
        # Try different encodings
        encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        
        for encoding in encodings:
            try:
                with path.open("rb") as f:
                    raw = f.read(self.sample_bytes)
                buf = raw.decode(encoding, errors="replace")
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            # Fallback
            encoding = "utf-8-sig"
            with path.open("rb") as f:
                raw = f.read(self.sample_bytes)
            buf = raw.decode(encoding, errors="replace")
        
        sniffer = csv.Sniffer()
        
        # Detect header
        try:
            has_header = sniffer.has_header(buf)
        except csv.Error:
            has_header = True
        
        # Detect dialect
        try:
            dialect = sniffer.sniff(buf, delimiters=[",", ";", "\t", "|"])
        except csv.Error:
            # Default CSV dialect
            class DefaultDialect(csv.Dialect):
                delimiter = ","
                doublequote = True
                escapechar = None
                lineterminator = "\n"
                quotechar = '"'
                quoting = csv.QUOTE_MINIMAL
                skipinitialspace = True
            
            dialect = DefaultDialect()
        
        return has_header, dialect, encoding
    
    def load_csv(self, path: Path) -> CSVDetection:
        """Load and analyze CSV file."""
        if not path.exists():
            raise CSVParsingError(f"CSV file not found: {path}")
        
        try:
            has_header, dialect, encoding = self.sniff_csv(path)
        except Exception as e:
            raise CSVParsingError(f"Failed to analyze CSV format: {e}") from e
        
        headers: List[str] = []
        rows: List[Dict[str, str]] = []
        
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                if has_header:
                    reader = csv.DictReader(f, dialect=dialect)
                    if reader.fieldnames:
                        headers = list(reader.fieldnames)
                else:
                    # Build synthetic headers for headerless CSV
                    plain_reader = csv.reader(f, dialect=dialect)
                    try:
                        first_row = next(plain_reader)
                        headers = [f"col_{i + 1}" for i in range(len(first_row))]
                        rows.append({h: v for h, v in zip(headers, first_row)})
                        reader = (dict(zip(headers, row)) for row in plain_reader)
                    except StopIteration:
                        raise CSVParsingError("CSV file appears to be empty")
                
                # Load preview rows
                for i, record in enumerate(reader):
                    if i >= self.max_preview_rows:
                        break
                    
                    # Clean and store row
                    clean_record = {
                        k: (v or "").strip() 
                        for k, v in record.items()
                    }
                    rows.append(clean_record)
        
        except Exception as e:
            raise CSVParsingError(f"Failed to read CSV file: {e}") from e
        
        if not headers:
            raise CSVParsingError("No headers found in CSV file")
        
        if not rows:
            raise CSVParsingError("No data rows found in CSV file")
        
        # Detect best columns
        artist_col, track_col, single_col = self._detect_columns(headers, rows)
        
        return CSVDetection(
            headers=headers,
            artist_col=artist_col,
            track_col=track_col,
            single_title_col=single_col,
            dialect=dialect,
            preview_rows=rows,
            encoding=encoding,
        )
    
    def _detect_columns(
        self, 
        headers: List[str], 
        rows: List[Dict[str, str]]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Detect the best artist and track columns."""
        
        # Score headers based on synonyms
        def score_header(name: str, synonyms: Set[str]) -> int:
            name_lower = name.strip().lower()
            score = 0
            
            # Exact matches get highest score
            if name_lower in synonyms:
                score += 10
            
            # Partial matches
            for synonym in synonyms:
                if synonym in name_lower:
                    score += max(1, len(synonym) // 3)
            
            # Bonus for common patterns
            if re.search(r"\bartist\b", name_lower):
                score += 3
            if re.search(r"\btitle\b|\btrack\b|\bsong\b", name_lower):
                score += 3
                
            return score
        
        # Calculate scores for all headers
        header_scores = {
            header: (
                score_header(header, ARTIST_SYNONYMS),
                score_header(header, TRACK_SYNONYMS)
            )
            for header in headers
        }
        
        # Find best artist and track columns
        best_artist_col = None
        best_artist_score = -1
        best_track_col = None
        best_track_score = -1
        
        for header in headers:
            artist_score, track_score = header_scores[header]
            
            if artist_score > best_artist_score:
                best_artist_col = header
                best_artist_score = artist_score
            
            if track_score > best_track_score:
                best_track_col = header
                best_track_score = track_score
        
        # If scores are too low, try single-column detection
        if best_artist_score <= 2 or best_track_score <= 2:
            single_col = self._detect_single_column(headers, rows)
            if single_col:
                return None, None, single_col
        
        # Avoid using same column for both artist and track
        if best_artist_col == best_track_col:
            # Find second-best track column
            second_best_track = None
            second_best_score = -1
            
            for header in headers:
                if header == best_artist_col:
                    continue
                    
                _, track_score = header_scores[header]
                if track_score > second_best_score:
                    second_best_track = header
                    second_best_score = track_score
            
            if second_best_track and second_best_score > 0:
                best_track_col = second_best_track
            else:
                # If no good alternative, prefer track column
                best_artist_col = None
        
        return best_artist_col, best_track_col, None
    
    def _detect_single_column(
        self,
        headers: List[str],
        rows: List[Dict[str, str]]
    ) -> Optional[str]:
        """Detect single column with 'Artist - Title' pattern."""
        
        best_column = None
        best_separator_count = 0
        
        for header in headers:
            separator_count = 0
            
            for row in rows:
                value = row.get(header, "")
                if any(sep in value for sep in SEPARATORS):
                    separator_count += 1
            
            # Need at least 30% of rows to have separators
            if separator_count > best_separator_count and separator_count >= len(rows) * 0.3:
                best_column = header
                best_separator_count = separator_count
        
        return best_column
    
    def parse_artist_title_from_single(self, value: str) -> Tuple[str, str]:
        """Parse artist and title from single column value."""
        value = (value or "").strip()
        
        # Try each separator
        for separator in SEPARATORS:
            if separator in value:
                parts = [p.strip() for p in value.split(separator, 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    return parts[0], parts[1]
        
        # Try quoted pattern: Artist "Title" 
        match = re.match(r'^(.*?)[""](.+?)[""]$', value)
        if match:
            artist = match.group(1).strip()
            title = match.group(2).strip()
            if artist and title:
                return artist, title
        
        # Fallback: assume it's just the title
        return "", value
    
    def build_track_items(
        self,
        detection: CSVDetection,
        artist_col_override: Optional[str] = None,
        track_col_override: Optional[str] = None,
    ) -> List[TrackItem]:
        """Build track items from CSV detection results."""
        
        tracks: List[TrackItem] = []
        
        # Use overrides if provided
        artist_col = artist_col_override or detection.artist_col
        track_col = track_col_override or detection.track_col
        single_col = detection.single_title_col
        
        for row in detection.preview_rows:
            artist = ""
            title = ""
            
            if single_col:
                # Single column mode
                artist, title = self.parse_artist_title_from_single(
                    row.get(single_col, "")
                )
            else:
                # Separate columns mode  
                artist = (row.get(artist_col, "") if artist_col else "").strip()
                title = (row.get(track_col, "") if track_col else "").strip()
            
            # Skip empty rows
            if not artist and not title:
                continue
            
            # Create search query
            query = f"{artist} - {title}".strip(" -")
            if not query:
                continue
            
            # Create filename stub
            stub = query or title or artist
            
            track = TrackItem(
                artist=artist,
                title=title,
                query=query,
                target_stub=stub,
            )
            
            tracks.append(track)
        
        return tracks
"""
Log File Parsing for Apache/Nginx Combined Format
"""

import re
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class LogEntry:
    """Represents a parsed log entry."""
    ip: str
    timestamp: datetime
    method: str
    url: str
    status: int
    size: int
    referrer: str
    user_agent: str

    def __post_init__(self):
        """Ensure types are correct."""
        if isinstance(self.status, str):
            self.status = int(self.status)
        if isinstance(self.size, str):
            self.size = int(self.size) if self.size != '-' else 0


class LogParser:
    """Parser for Apache/Nginx combined log format."""

    # Pattern for combined log format:
    # IP - - [timestamp] "METHOD URL HTTP/x.x" STATUS SIZE "referrer" "user-agent"
    COMBINED_FORMAT = re.compile(
        r'(?P<ip>[\d\.]+)\s+-\s+-\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<method>\w+)\s+(?P<url>[^\s]+)\s+HTTP/[\d\.]+"\s+'
        r'(?P<status>\d+)\s+'
        r'(?P<size>\d+|-)\s+'
        r'"(?P<referrer>[^"]*)"\s+'
        r'"(?P<user_agent>[^"]*)"'
    )

    # Alternative patterns for edge cases
    SIMPLE_FORMAT = re.compile(
        r'(?P<ip>[\d\.]+)\s+\S+\s+\S+\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<method>\w+)\s+(?P<url>\S+)[^"]*"\s+'
        r'(?P<status>\d+)\s+'
        r'(?P<size>\d+|-)'
    )

    # Timestamp formats to try
    TIMESTAMP_FORMATS = [
        '%d/%b/%Y:%H:%M:%S %z',      # 10/Jan/2025:14:30:00 +0000
        '%d/%b/%Y:%H:%M:%S',          # 10/Jan/2025:14:30:00
        '%Y-%m-%d %H:%M:%S',          # 2025-01-10 14:30:00
    ]

    def parse(self, line: str) -> Optional[dict]:
        """
        Parse a single log line.

        Returns a dictionary with parsed fields or None if parsing fails.
        """
        line = line.strip()
        if not line:
            return None

        # Try combined format first
        match = self.COMBINED_FORMAT.match(line)

        if not match:
            # Try simple format as fallback
            match = self.SIMPLE_FORMAT.match(line)
            if match:
                data = match.groupdict()
                data['referrer'] = '-'
                data['user_agent'] = ''
            else:
                return None
        else:
            data = match.groupdict()

        # Parse timestamp
        timestamp = self._parse_timestamp(data['timestamp'])
        if timestamp is None:
            return None
        data['timestamp'] = timestamp

        # Parse status code
        try:
            data['status'] = int(data['status'])
        except (ValueError, TypeError):
            return None

        # Parse size
        try:
            data['size'] = int(data['size']) if data['size'] != '-' else 0
        except (ValueError, TypeError):
            data['size'] = 0

        return data

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string with multiple format support."""
        for fmt in self.TIMESTAMP_FORMATS:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # Try stripping timezone if still failing
        try:
            # Handle case where timezone is at end: "10/Jan/2025:14:30:00 +0000"
            ts_parts = timestamp_str.rsplit(' ', 1)
            if len(ts_parts) == 2:
                return datetime.strptime(ts_parts[0], '%d/%b/%Y:%H:%M:%S')
        except ValueError:
            pass

        return None

    def parse_file(self, file_path: str):
        """
        Generator that parses all lines in a file.

        Yields parsed entries, skipping invalid lines.
        """
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                entry = self.parse(line)
                if entry is not None:
                    yield entry

    def parse_to_entry(self, line: str) -> Optional[LogEntry]:
        """Parse a line and return a LogEntry object."""
        data = self.parse(line)
        if data is None:
            return None

        return LogEntry(
            ip=data['ip'],
            timestamp=data['timestamp'],
            method=data['method'],
            url=data['url'],
            status=data['status'],
            size=data['size'],
            referrer=data.get('referrer', '-'),
            user_agent=data.get('user_agent', '')
        )

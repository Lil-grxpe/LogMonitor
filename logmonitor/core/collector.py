"""Log collection module for batch and streaming log processing."""

import os
import time
from abc import ABC, abstractmethod
from typing import Iterator, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


class LogCollector(ABC):
    """Abstract base class for log collectors."""
    
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self._validate_path()
    
    def _validate_path(self) -> None:
        if not self.log_path.exists():
            raise FileNotFoundError(f"File {self.log_path} not found")
        if not os.access(self.log_path, os.R_OK):
            raise PermissionError(f"No read permission for {self.log_path}")
    
    @abstractmethod
    def collect_batch(self) -> Iterator[str]:
        pass
    
    def collect_streaming(self, callback) -> None:
        event_handler = LogFileEventHandler(self.log_path, callback)
        observer = Observer()
        observer.schedule(event_handler, str(self.log_path.parent), recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


class LogFileEventHandler(FileSystemEventHandler):
    """Event handler for file modifications using watchdog."""
    
    def __init__(self, log_path: Path, callback):
        self.log_path = log_path
        self.callback = callback
        self.last_position = 0
        
        if self.log_path.exists():
            with open(self.log_path, 'r') as f:
                f.seek(0, os.SEEK_END)
                self.last_position = f.tell()
    
    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent) and Path(event.src_path) == self.log_path:
            self._read_new_lines()
    
    def _read_new_lines(self):
        try:
            with open(self.log_path, 'r') as f:
                f.seek(self.last_position)
                for line in f:
                    if line.strip():
                        self.callback(line.rstrip('\n'))
                self.last_position = f.tell()
        except Exception as e:
            print(f"Error reading new lines: {e}")


class AuthLogCollector(LogCollector):
    """Collector for auth.log files."""
    
    def collect_batch(self) -> Iterator[str]:
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():
                        yield line
        except Exception as e:
            raise IOError(f"Error reading {self.log_path}: {e}")


class SyslogCollector(LogCollector):
    """Collector for syslog files."""
    
    def collect_batch(self) -> Iterator[str]:
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():
                        yield line
        except Exception as e:
            raise IOError(f"Error reading {self.log_path}: {e}")


class GenericLogCollector(LogCollector):
    """Generic collector for any log file."""
    
    def collect_batch(self) -> Iterator[str]:
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():
                        yield line
        except Exception as e:
            raise IOError(f"Error reading {self.log_path}: {e}")


def create_collector(log_path: str) -> LogCollector:
    """Factory function to create appropriate log collector."""
    path = Path(log_path)
    
    if 'auth.log' in path.name:
        return AuthLogCollector(log_path)
    elif 'syslog' in path.name:
        return SyslogCollector(log_path)
    else:
        return GenericLogCollector(log_path)

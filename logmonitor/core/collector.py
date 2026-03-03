"""Log collection module for batch and streaming log processing."""

import os
import time
import subprocess
import threading
from abc import ABC, abstractmethod
from typing import Iterator, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


# ─── Journald source identifiers ──────────────────────────────────────────────
JOURNALD_FILTERS = {
    'journald://auth': [
        '_COMM=sshd', '_COMM=sudo', '_COMM=su', '_COMM=login',
        '_COMM=passwd', '_COMM=useradd', '_COMM=userdel', '_COMM=groupadd',
        'SYSLOG_IDENTIFIER=sshd', 'SYSLOG_IDENTIFIER=sudo',
    ],
    'journald://system': [],  # No filter: all system messages
}


class LogCollector(ABC):
    """Abstract base class for log collectors."""

    @abstractmethod
    def collect_batch(self) -> Iterator[str]:
        pass

    @abstractmethod
    def collect_streaming(self, callback) -> None:
        pass


class FileLogCollector(LogCollector):
    """Base collector for flat log files (auth.log, syslog, etc.)."""

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self._validate_path()

    def _validate_path(self) -> None:
        if not self.log_path.exists():
            raise FileNotFoundError(f"File {self.log_path} not found")
        if not os.access(self.log_path, os.R_OK):
            raise PermissionError(f"No read permission for {self.log_path}")

    def collect_batch(self) -> Iterator[str]:
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():
                        yield line
        except Exception as e:
            raise IOError(f"Error reading {self.log_path}: {e}")

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


class JournaldCollector(LogCollector):
    """
    Collector for systemd-journald.

    Uses 'journalctl -o short-iso' for machine-readable output with ISO timestamps.
    Supports streaming mode via 'journalctl -f'.

    source_key: one of 'journald://auth' or 'journald://system'
    """

    def __init__(self, source_key: str = 'journald://auth', since: str = '1 hour ago'):
        self.source_key = source_key
        self.since = since
        self._stop_event = threading.Event()

    def _build_cmd(self, follow: bool = False, lines: int = 1000) -> list:
        cmd = ['journalctl', '--no-pager', '-o', 'short-iso']

        if follow:
            cmd.append('-f')
        else:
            # Batch: use --since + -n, no identifier filters (they time out on large journals)
            cmd += ['--since', self.since, f'-n', str(lines)]

        # Only apply auth service filters in streaming mode to reduce noise
        if follow and self.source_key == 'journald://auth':
            cmd += [
                '--identifier=sshd', '--identifier=sudo', '--identifier=su',
                '--identifier=login', '--identifier=passwd',
                '--identifier=useradd', '--identifier=userdel',
                '--identifier=groupadd', '--identifier=cron'
            ]

        return cmd

    def collect_batch(self) -> Iterator[str]:
        """Collect recent journald entries (last hour or up to 1000 lines)."""
        cmd = self._build_cmd(follow=False)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Increased: large journals can be slow
            )
            if result.returncode != 0 and result.stderr:
                print(f"[JournaldCollector] Warning: {result.stderr.strip()}")

            for line in result.stdout.splitlines():
                line = line.strip()
                if line and not line.startswith('--'):  # skip separator lines
                    yield line

        except FileNotFoundError:
            raise RuntimeError("journalctl not found — is systemd installed?")
        except subprocess.TimeoutExpired:
            raise RuntimeError("journalctl timed out during batch collection (journal too large?)")

    def collect_streaming(self, callback) -> None:
        """Stream new journald entries in real time using 'journalctl -f'."""
        cmd = self._build_cmd(follow=True)
        self._stop_event.clear()

        while not self._stop_event.is_set():
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # line-buffered
                )

                for line in proc.stdout:
                    if self._stop_event.is_set():
                        proc.terminate()
                        break
                    line = line.rstrip('\n').strip()
                    if line and not line.startswith('--'):
                        callback(line)

                # If subprocess died unexpectedly, wait and retry
                proc.wait()
                if not self._stop_event.is_set():
                    print("[JournaldCollector] journalctl -f exited unexpectedly, restarting in 3s...")
                    time.sleep(3)

            except FileNotFoundError:
                print("[JournaldCollector] ERROR: journalctl not found")
                break
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"[JournaldCollector] Streaming error: {e}, retrying in 3s...")
                    time.sleep(3)

    def stop(self):
        """Signal the streaming loop to stop."""
        self._stop_event.set()


# ─── Legacy typed collectors (keep for compatibility) ─────────────────────────

class AuthLogCollector(FileLogCollector):
    """Collector for auth.log files."""
    pass


class SyslogCollector(FileLogCollector):
    """Collector for syslog files."""
    pass


class GenericLogCollector(FileLogCollector):
    """Generic collector for any log file."""
    pass


# ─── Factory ──────────────────────────────────────────────────────────────────

def create_collector(log_path: str) -> LogCollector:
    """
    Factory function to create appropriate log collector.

    Recognizes:
      - 'journald://auth'   → JournaldCollector (auth services only)
      - 'journald://system' → JournaldCollector (all system messages)
      - Any file path       → FileLogCollector variant
    """
    if log_path.startswith('journald://'):
        return JournaldCollector(source_key=log_path)

    path = Path(log_path)

    if 'auth' in path.name:
        return AuthLogCollector(log_path)
    elif 'syslog' in path.name:
        return SyslogCollector(log_path)
    else:
        return GenericLogCollector(log_path)

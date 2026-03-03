"""Log normalization module for parsing raw log lines."""

import re
import json
from datetime import datetime
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


class LogNormalizer(ABC):
    """Abstract base class for log normalizers."""

    @abstractmethod
    def normalize(self, raw_line: str) -> Optional[Dict[str, Any]]:
        pass

    def _extract_timestamp(self, timestamp_str: str) -> str:
        # Try ISO format first (journald short-iso: 2026-03-03T14:30:00+0100)
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.isoformat()
            except ValueError:
                pass

        # Classic syslog format: "Mar  3 14:30:00"
        try:
            dt = datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
            dt = dt.replace(year=datetime.now().year)
            return dt.isoformat()
        except ValueError:
            pass

        return datetime.now().isoformat()


class AuthLogNormalizer(LogNormalizer):
    """Normalizer for auth.log format (classic syslog timestamps)."""

    PATTERNS = {
        'ssh_failed': re.compile(
            r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[\d+\])?: '
            r'Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)'
        ),
        'ssh_accepted': re.compile(
            r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[\d+\])?: '
            r'Accepted (?:password|publickey) for (\S+) from (\d+\.\d+\.\d+\.\d+)'
        ),
        'ssh_disconnected': re.compile(
            r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[\d+\])?: '
            r'Disconnected from (?:invalid user )?(\S+)? ?(\d+\.\d+\.\d+\.\d+)'
        ),
        'sudo': re.compile(
            r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+sudo(?:\[\d+\])?: '
            r'(\S+) : TTY=(\S+) ; PWD=(\S+) ; USER=(\S+) ; COMMAND=(.+)'
        ),
        'sudo_failed': re.compile(
            r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+sudo(?:\[\d+\])?: '
            r'(?:.+ : )?(\d+) incorrect password attempts'
        ),
        'generic': re.compile(
            r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[\d+\])?: (.+)'
        )
    }

    def normalize(self, raw_line: str) -> Optional[Dict[str, Any]]:
        if not raw_line or not raw_line.strip():
            return None

        for pattern_name, pattern in self.PATTERNS.items():
            match = pattern.match(raw_line)
            if match:
                return self._parse_match(pattern_name, match, raw_line)

        return {
            'timestamp': datetime.now().isoformat(),
            'hostname': 'unknown',
            'service': 'unknown',
            'level': 'info',
            'message': raw_line,
            'raw': raw_line
        }

    def _parse_match(self, pattern_name: str, match: re.Match, raw_line: str) -> Dict[str, Any]:
        if pattern_name == 'ssh_failed':
            timestamp, hostname, service, user, ip = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': 'warning',
                'event_type': 'ssh_failed_login',
                'message': f'Failed password for {user} from {ip}',
                'user': user,
                'source_ip': ip,
                'raw': raw_line
            }

        elif pattern_name == 'ssh_accepted':
            timestamp, hostname, service, user, ip = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': 'info',
                'event_type': 'ssh_accepted_login',
                'message': f'Accepted login for {user} from {ip}',
                'user': user,
                'source_ip': ip,
                'raw': raw_line
            }

        elif pattern_name == 'sudo':
            timestamp, hostname, user, tty, pwd, target_user, command = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': 'sudo',
                'level': 'info' if target_user != 'root' else 'warning',
                'event_type': 'sudo_command',
                'message': f'{user} executed sudo command as {target_user}',
                'user': user,
                'target_user': target_user,
                'command': command,
                'raw': raw_line
            }

        elif pattern_name == 'sudo_failed':
            timestamp, hostname, attempts = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': 'sudo',
                'level': 'warning',
                'event_type': 'sudo_failed',
                'message': f'Sudo authentication failed ({attempts} attempts)',
                'attempts': int(attempts),
                'raw': raw_line
            }

        elif pattern_name == 'generic':
            timestamp, hostname, service, message = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': 'info',
                'message': message,
                'raw': raw_line
            }

        return None


class JournaldNormalizer(LogNormalizer):
    """
    Normalizer for journald short-iso format output.

    Example line:
      2026-03-03T14:30:00+0100 hostname sshd[1234]: Failed password for invalid user admin from 192.168.1.1 port 22 ssh2
    """

    # ISO timestamp: 2026-03-03T14:30:00+0100 or 2026-03-03T14:30:00+01:00
    _TS = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:?\d{2})'

    PATTERNS = {
        'ssh_failed': re.compile(
            _TS + r'\s+(\S+)\s+(\S+?)(?:\[\d+\])?: '
            r'Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)'
        ),
        'ssh_accepted': re.compile(
            _TS + r'\s+(\S+)\s+(\S+?)(?:\[\d+\])?: '
            r'Accepted (?:password|publickey) for (\S+) from (\d+\.\d+\.\d+\.\d+)'
        ),
        'ssh_disconnected': re.compile(
            _TS + r'\s+(\S+)\s+(\S+?)(?:\[\d+\])?: '
            r'Disconnected from (?:invalid user )?(\S+)? ?(\d+\.\d+\.\d+\.\d+)'
        ),
        'sudo': re.compile(
            _TS + r'\s+(\S+)\s+sudo(?:\[\d+\])?: '
            r'(\S+) : TTY=(\S+) ; PWD=(\S+) ; USER=(\S+) ; COMMAND=(.+)'
        ),
        'sudo_failed': re.compile(
            _TS + r'\s+(\S+)\s+sudo(?:\[\d+\])?: '
            r'(?:.+ : )?(\d+) incorrect password attempts'
        ),
        'generic': re.compile(
            _TS + r'\s+(\S+)\s+(\S+?)(?:\[\d+\])?: (.+)'
        ),
    }

    def normalize(self, raw_line: str) -> Optional[Dict[str, Any]]:
        if not raw_line or not raw_line.strip():
            return None

        # Skip journald separator or metadata lines
        if raw_line.startswith('--') or raw_line.startswith('Hint:'):
            return None

        for pattern_name, pattern in self.PATTERNS.items():
            match = pattern.match(raw_line)
            if match:
                return self._parse_match(pattern_name, match, raw_line)

        # Fallback: return generic event if nothing matched
        return {
            'timestamp': datetime.now().isoformat(),
            'hostname': 'unknown',
            'service': 'journald',
            'level': 'info',
            'message': raw_line,
            'raw': raw_line
        }

    def _parse_match(self, pattern_name: str, match: re.Match, raw_line: str) -> Dict[str, Any]:
        if pattern_name == 'ssh_failed':
            timestamp, hostname, service, user, ip = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': 'warning',
                'event_type': 'ssh_failed_login',
                'message': f'Failed password for {user} from {ip}',
                'user': user,
                'source_ip': ip,
                'raw': raw_line
            }

        elif pattern_name == 'ssh_accepted':
            timestamp, hostname, service, user, ip = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': 'info',
                'event_type': 'ssh_accepted_login',
                'message': f'Accepted login for {user} from {ip}',
                'user': user,
                'source_ip': ip,
                'raw': raw_line
            }

        elif pattern_name == 'sudo':
            timestamp, hostname, user, tty, pwd, target_user, command = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': 'sudo',
                'level': 'info' if target_user != 'root' else 'warning',
                'event_type': 'sudo_command',
                'message': f'{user} executed sudo command as {target_user}',
                'user': user,
                'target_user': target_user,
                'command': command,
                'raw': raw_line
            }

        elif pattern_name == 'sudo_failed':
            timestamp, hostname, attempts = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': 'sudo',
                'level': 'warning',
                'event_type': 'sudo_failed',
                'message': f'Sudo authentication failed ({attempts} attempts)',
                'attempts': int(attempts),
                'raw': raw_line
            }

        elif pattern_name == 'generic':
            timestamp, hostname, service, message = match.groups()
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': self._detect_level(message),
                'message': message,
                'raw': raw_line
            }

        return None

    def _detect_level(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ['error', 'failed', 'failure', 'critical', 'denied']):
            return 'error'
        elif any(w in msg for w in ['warning', 'warn']):
            return 'warning'
        elif any(w in msg for w in ['debug']):
            return 'debug'
        return 'info'


class SyslogNormalizer(LogNormalizer):
    """Normalizer for syslog format."""

    PATTERN = re.compile(
        r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[\d+\])?: (.+)'
    )

    def normalize(self, raw_line: str) -> Optional[Dict[str, Any]]:
        if not raw_line or not raw_line.strip():
            return None

        match = self.PATTERN.match(raw_line)
        if match:
            timestamp, hostname, service, message = match.groups()
            level = self._detect_level(message)

            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': level,
                'message': message,
                'raw': raw_line
            }

        return {
            'timestamp': datetime.now().isoformat(),
            'hostname': 'unknown',
            'service': 'unknown',
            'level': 'info',
            'message': raw_line,
            'raw': raw_line
        }

    def _detect_level(self, message: str) -> str:
        message_lower = message.lower()

        if any(word in message_lower for word in ['error', 'failed', 'failure', 'critical']):
            return 'error'
        elif any(word in message_lower for word in ['warning', 'warn']):
            return 'warning'
        elif any(word in message_lower for word in ['debug']):
            return 'debug'
        else:
            return 'info'


def create_normalizer(log_type: str) -> LogNormalizer:
    """Factory function to create appropriate normalizer."""
    log_type_lower = log_type.lower()

    if 'journald' in log_type_lower:
        return JournaldNormalizer()
    elif 'auth' in log_type_lower:
        return AuthLogNormalizer()
    elif 'syslog' in log_type_lower:
        return SyslogNormalizer()
    else:
        return SyslogNormalizer()


def normalize_to_json(raw_line: str, log_type: str = 'auth') -> Optional[str]:
    """Helper to normalize and convert to JSON string."""
    normalizer = create_normalizer(log_type)
    normalized = normalizer.normalize(raw_line)

    if normalized:
        return json.dumps(normalized, ensure_ascii=False)
    return None

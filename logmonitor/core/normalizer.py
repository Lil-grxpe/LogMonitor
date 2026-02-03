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
        try:
            dt = datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
            dt = dt.replace(year=datetime.now().year)
            return dt.isoformat()
        except ValueError:
            return datetime.now().isoformat()


class AuthLogNormalizer(LogNormalizer):
    """Normalizer for auth.log format."""
    
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
    if 'auth' in log_type.lower():
        return AuthLogNormalizer()
    elif 'syslog' in log_type.lower():
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

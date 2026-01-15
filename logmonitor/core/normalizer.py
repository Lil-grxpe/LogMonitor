"""
Module de normalisation de logs (F1)
Responsable : Melkior AGUESSI

Ce module convertit les lignes de logs brutes en format JSON structuré
"""

import re
import json
from datetime import datetime
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


class LogNormalizer(ABC):
    """Classe abstraite de base pour tous les normaliseurs"""
    
    @abstractmethod
    def normalize(self, raw_line: str) -> Optional[Dict[str, Any]]:
        """
        Normalise une ligne de log brute en dictionnaire JSON
        
        Args:
            raw_line: Ligne de log brute
        
        Returns:
            Dict contenant les champs normalisés, ou None si parsing échoue
        """
        pass
    
    def _extract_timestamp(self, timestamp_str: str) -> str:
        """
        Extrait et normalise le timestamp
        
        Args:
            timestamp_str: String contenant le timestamp
        
        Returns:
            Timestamp au format ISO 8601
        """
        try:
            # Format syslog: Dec 30 12:34:56
            dt = datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
            # Ajouter l'année courante
            dt = dt.replace(year=datetime.now().year)
            return dt.isoformat()
        except ValueError:
            # Retourner timestamp actuel si parsing échoue
            return datetime.now().isoformat()


class AuthLogNormalizer(LogNormalizer):
    """Normaliseur spécialisé pour auth.log"""
    
    # Patterns regex pour parser auth.log
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
        """
        Normalise une ligne de auth.log
        
        Args:
            raw_line: Ligne brute de auth.log
        
        Returns:
            Dictionnaire avec les champs normalisés
        """
        if not raw_line or not raw_line.strip():
            return None
        
        # Essayer chaque pattern
        for pattern_name, pattern in self.PATTERNS.items():
            match = pattern.match(raw_line)
            if match:
                return self._parse_match(pattern_name, match, raw_line)
        
        # Si aucun pattern ne correspond, retourner structure basique
        return {
            'timestamp': datetime.now().isoformat(),
            'hostname': 'unknown',
            'service': 'unknown',
            'level': 'info',
            'message': raw_line,
            'raw': raw_line
        }
    
    def _parse_match(self, pattern_name: str, match: re.Match, raw_line: str) -> Dict[str, Any]:
        """Parse un match regex selon le type de pattern"""
        
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
    """Normaliseur spécialisé pour syslog"""
    
    PATTERN = re.compile(
        r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[\d+\])?: (.+)'
    )
    
    def normalize(self, raw_line: str) -> Optional[Dict[str, Any]]:
        """
        Normalise une ligne de syslog
        
        Args:
            raw_line: Ligne brute de syslog
        
        Returns:
            Dictionnaire avec les champs normalisés
        """
        if not raw_line or not raw_line.strip():
            return None
        
        match = self.PATTERN.match(raw_line)
        if match:
            timestamp, hostname, service, message = match.groups()
            
            # Déterminer le niveau de sévérité depuis le message
            level = self._detect_level(message)
            
            return {
                'timestamp': self._extract_timestamp(timestamp),
                'hostname': hostname,
                'service': service,
                'level': level,
                'message': message,
                'raw': raw_line
            }
        
        # Fallback si parsing échoue
        return {
            'timestamp': datetime.now().isoformat(),
            'hostname': 'unknown',
            'service': 'unknown',
            'level': 'info',
            'message': raw_line,
            'raw': raw_line
        }
    
    def _detect_level(self, message: str) -> str:
        """Détecte le niveau de sévérité depuis le message"""
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
    """
    Factory function pour créer le bon type de normaliseur
    
    Args:
        log_type: Type de log ('auth', 'syslog', etc.)
    
    Returns:
        LogNormalizer: Instance appropriée du normaliseur
    """
    if 'auth' in log_type.lower():
        return AuthLogNormalizer()
    elif 'syslog' in log_type.lower():
        return SyslogNormalizer()
    else:
        return SyslogNormalizer()  # Default to syslog format


def normalize_to_json(raw_line: str, log_type: str = 'auth') -> Optional[str]:
    """
    Fonction helper pour normaliser et convertir en JSON string
    
    Args:
        raw_line: Ligne brute
        log_type: Type de log
    
    Returns:
        String JSON, ou None si échec
    """
    normalizer = create_normalizer(log_type)
    normalized = normalizer.normalize(raw_line)
    
    if normalized:
        return json.dumps(normalized, ensure_ascii=False)
    return None

"""Security detection rules for log analysis."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import dateutil.parser


class DetectionRule(ABC):
    """Abstract base class for detection rules."""
    
    def __init__(self, name: str, severity: str, config: Dict[str, Any]):
        self.name = name
        self.severity = severity
        self.config = config
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        pass
    
    def _create_alert(self, event: Dict[str, Any], description: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'timestamp': datetime.now().isoformat(),
            'rule_name': self.name,
            'severity': self.severity,
            'description': description,
            'event': event,
            'evidence': evidence
        }


class BruteForceSSHRule(DetectionRule):
    """Detects SSH brute force attacks."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('BruteForce SSH', config.get('severity', 'high'), config)
        self.threshold = config.get('threshold', 5)
        self.time_window = config.get('time_window', 300)
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'ssh_failed_login':
            return None
        
        source_ip = event.get('source_ip')
        if not source_ip:
            return None
        
        context.add_failed_login(source_ip, event)
        current_time = context._get_event_time(event)
        recent_failures = context.get_recent_failed_logins(source_ip, self.time_window, current_time)
        
        if len(recent_failures) >= self.threshold:
            if context.should_alert(f"bruteforce_{source_ip}", self.time_window, current_time):
                return self._create_alert(
                    event,
                    f"SSH bruteforce detected: {len(recent_failures)} failed attempts from {source_ip} in {self.time_window}s",
                    {
                        'source_ip': source_ip,
                        'failed_attempts': len(recent_failures),
                        'time_window': self.time_window,
                        'attempts_details': recent_failures[-5:]
                    }
                )
        
        return None


class MultipleAccountsRule(DetectionRule):
    """Detects attacks targeting multiple accounts."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Multiple Accounts Attack', config.get('severity', 'medium'), config)
        self.threshold = config.get('threshold', 3)
        self.time_window = config.get('time_window', 600)
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'ssh_failed_login':
            return None
        
        source_ip = event.get('source_ip')
        user = event.get('user')
        if not source_ip or not user:
            return None
        
        context.add_targeted_user(source_ip, user, event)
        current_time = context._get_event_time(event)
        targeted_users = context.get_recent_targeted_users(source_ip, self.time_window, current_time)
        
        if len(targeted_users) >= self.threshold:
            if context.should_alert(f"multiple_accounts_{source_ip}", self.time_window, current_time):
                return self._create_alert(
                    event,
                    f"Multiple accounts attack: {len(targeted_users)} accounts targeted from {source_ip}",
                    {
                        'source_ip': source_ip,
                        'targeted_accounts': list(targeted_users.keys()),
                        'total_attempts': sum(len(attempts) for attempts in targeted_users.values())
                    }
                )
        
        return None


class SuspiciousRootLoginRule(DetectionRule):
    """Detects suspicious root logins."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Suspicious Root Login', config.get('severity', 'high'), config)
        self.allowed_sources = set(config.get('allowed_sources', []))
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'ssh_accepted_login':
            return None
        
        user = event.get('user')
        source_ip = event.get('source_ip')
        
        if user != 'root':
            return None
        
        if self.allowed_sources and source_ip in self.allowed_sources:
            return None
        
        current_time = context._get_event_time(event)
        
        if context.should_alert(f"root_login_{source_ip}", 3600, current_time):
             return self._create_alert(
                event,
                f"Suspicious root login from {source_ip}",
                {
                    'user': user,
                    'source_ip': source_ip,
                    'hostname': event.get('hostname'),
                    'allowed_sources': list(self.allowed_sources) if self.allowed_sources else "none"
                }
            )
        
        return None


class SensitiveFileModificationRule(DetectionRule):
    """Detects access to sensitive system files."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Sensitive File Modification', config.get('severity', 'critical'), config)
        self.watched_files = set(config.get('watched_files', [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/sudoers',
            '/etc/ssh/sshd_config'
        ]))
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        message = (event.get('message', '') + ' ' + event.get('command', '')).lower()
        keywords = ['edit', 'modif', 'change', 'write', 'alter', 'update', 'vim', 'nano', 'vi', 'emacs']
        
        for watched_file in self.watched_files:
            if watched_file.lower() in message:
                if any(keyword in message for keyword in keywords):
                    return self._create_alert(
                        event,
                        f"Sensitive file access detected: {watched_file}",
                        {
                            'file': watched_file,
                            'user': event.get('user', 'unknown'),
                            'hostname': event.get('hostname'),
                            'service': event.get('service'),
                            'command': event.get('command', 'unknown')
                        }
                    )
        
        return None


class ActivitySpikeRule(DetectionRule):
    """Detects unusual activity spikes."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Activity Spike', config.get('severity', 'medium'), config)
        self.threshold_multiplier = config.get('threshold_multiplier', 3.0)
        self.baseline_window = config.get('baseline_window', 3600)
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        context.add_event_count(event)
        current_time = context._get_event_time(event)
        recent_counts = context.get_event_counts(self.baseline_window, current_time)
        
        if len(recent_counts) < 10:
            return None
        
        baseline = recent_counts[:-1]
        current = recent_counts[-1]
        
        if not baseline:
            return None
        
        avg_baseline = statistics.mean(baseline)
        
        if avg_baseline > 0 and current >= (avg_baseline * self.threshold_multiplier):
            if context.should_alert("activity_spike", 600, current_time):
                return self._create_alert(
                    event,
                    f"Activity spike: {current} events (average: {avg_baseline:.1f})",
                    {
                        'current_rate': current,
                        'baseline_average': avg_baseline,
                        'multiplier': current / avg_baseline if avg_baseline > 0 else 0,
                        'threshold': self.threshold_multiplier
                    }
                )
        
        return None


class UnusualLoginTimeRule(DetectionRule):
    """Detects logins during unusual hours."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Unusual Login Time', config.get('severity', 'medium'), config)
        # Format: "HH:MM-HH:MM" (24h)
        self.unusual_hours = config.get('unusual_hours', ["23:00-05:00"])
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        if event.get('event_type') not in ['ssh_accepted_login', 'ssh_failed_login']:
            return None
        
        event_time = context._get_event_time(event)
        current_hour = event_time.time()
        
        is_unusual = False
        time_range = ""
        
        for window in self.unusual_hours:
            try:
                start_str, end_str = window.split('-')
                start = datetime.strptime(start_str, "%H:%M").time()
                end = datetime.strptime(end_str, "%H:%M").time()
                
                if start <= end:
                    if start <= current_hour <= end:
                        is_unusual = True
                        time_range = window
                        break
                else:  # Crosses midnight (e.g. 23:00-05:00)
                    if current_hour >= start or current_hour <= end:
                        is_unusual = True
                        time_range = window
                        break
            except ValueError:
                continue
        
        if is_unusual:
            # Avoid spamming alerts for the same user/IP in the same hour
            key = f"unusual_time_{event.get('user')}_{event.get('source_ip')}_{event_time.hour}"
            if context.should_alert(key, 3600, event_time):
                return self._create_alert(
                    event,
                    f"Login attempt during unusual hours ({current_hour.strftime('%H:%M')})",
                    {
                        'time': current_hour.strftime('%H:%M'),
                        'unusual_window': time_range,
                        'user': event.get('user', 'unknown'),
                        'source_ip': event.get('source_ip', 'unknown')
                    }
                )
        
        return None


class SudoFailureRule(DetectionRule):
    """Detects repeated sudo failures."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Sudo Failure', config.get('severity', 'high'), config)
        self.threshold = config.get('threshold', 3)
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'sudo_failed':
            return None
        
        user = event.get('user', 'unknown') or event.get('message', '').split(' ')[0]
        attempts = event.get('attempts', 1)
        
        if attempts >= self.threshold:
            return self._create_alert(
                event,
                f"Excessive sudo failures by user {user}",
                {
                    'user': user,
                    'failed_attempts': attempts,
                    'threshold': self.threshold
                }
            )
        
        return None


class UnknownUserRule(DetectionRule):
    """Detects login attempts with unknown usernames."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Unknown User Login', config.get('severity', 'medium'), config)
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'ssh_failed_login':
            return None
        
        raw_msg = event.get('raw', '').lower()
        if 'invalid user' in raw_msg:
            user = event.get('user')
            source_ip = event.get('source_ip')
            
            key = f"unknown_user_{user}_{source_ip}"
            # Alert max once per hour per user/IP combination to avoid flooding from brute force
            if context.should_alert(key, 3600, context._get_event_time(event)):
                return self._create_alert(
                    event,
                    f"Invalid user login attempt: {user}",
                    {
                        'user': user,
                        'source_ip': source_ip,
                        'message': 'Attempt to log in with non-existent user'
                    }
                )
        
        return None


class DetectionContext:
    """Shared context for detection rules."""
    
    def __init__(self):
        self.failed_logins: Dict[str, List[Dict]] = defaultdict(list)
        self.targeted_users: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        self.event_counts: List[Dict[str, Any]] = []
        self.alert_history: Dict[str, datetime] = {}
        self.last_cleanup = datetime.now()

    def _get_event_time(self, event: Dict[str, Any]) -> datetime:
        """Parse event timestamp and return a timezone-naive datetime.

        Journald produces ISO timestamps with timezone offsets (e.g. +0100).
        All internal comparisons use naive datetimes (local time without tz),
        so we strip tzinfo after converting to local time.
        """
        ts = event.get('timestamp')
        if isinstance(ts, datetime):
            # Already a datetime: strip timezone if present
            return ts.replace(tzinfo=None) if ts.tzinfo is not None else ts
        try:
            dt = datetime.fromisoformat(str(ts))
            # Convert to naive: remove tzinfo (we keep local wall-clock time)
            return dt.replace(tzinfo=None)
        except (ValueError, TypeError):
            return datetime.now()

    def add_failed_login(self, source_ip: str, event: Dict[str, Any]):
        event_time = self._get_event_time(event)
        self.failed_logins[source_ip].append({
            'timestamp': event_time,
            'event': event
        })
        self._cleanup_if_needed(event_time)
    
    def get_recent_failed_logins(self, source_ip: str, time_window: int, current_time: datetime = None) -> List[Dict]:
        if current_time is None:
            current_time = datetime.now()
            
        cutoff = current_time - timedelta(seconds=time_window)
        return [
            item for item in self.failed_logins[source_ip]
            if item['timestamp'] > cutoff
        ]
    
    def add_targeted_user(self, source_ip: str, user: str, event: Dict[str, Any]):
        event_time = self._get_event_time(event)
        self.targeted_users[source_ip][user].append({
            'timestamp': event_time,
            'event': event
        })
        self._cleanup_if_needed(event_time)
    
    def get_recent_targeted_users(self, source_ip: str, time_window: int, current_time: datetime = None) -> Dict[str, List]:
        if current_time is None:
            current_time = datetime.now()
            
        cutoff = current_time - timedelta(seconds=time_window)
        result = defaultdict(list)
        
        for user, attempts in self.targeted_users[source_ip].items():
            recent = [a for a in attempts if a['timestamp'] > cutoff]
            if recent:
                result[user] = recent
        
        return dict(result)
    
    def add_event_count(self, event: Dict[str, Any]):
        event_time = self._get_event_time(event)
        current_minute = event_time.replace(second=0, microsecond=0)
        
        for entry in self.event_counts:
            if entry['minute'] == current_minute:
                entry['count'] += 1
                return
        
        self.event_counts.append({
            'minute': current_minute,
            'count': 1
        })
    
    def get_event_counts(self, time_window: int, current_time: datetime = None) -> List[int]:
        if current_time is None:
            current_time = datetime.now()
            
        cutoff = current_time - timedelta(seconds=time_window)
        
        relevant_counts = [
            entry for entry in self.event_counts
            if entry['minute'] > cutoff and entry['minute'] <= current_time
        ]
        relevant_counts.sort(key=lambda x: x['minute'])
        
        return [entry['count'] for entry in relevant_counts]
        
    def should_alert(self, key: str, cooldown: int, current_time: datetime = None) -> bool:
        if current_time is None:
            current_time = datetime.now()

        last_alert = self.alert_history.get(key)
        
        if last_alert is None or (current_time - last_alert).total_seconds() > cooldown:
            self.alert_history[key] = current_time
            return True
        
        return False
    
    def _cleanup_if_needed(self, current_time: datetime = None):
        if current_time is None:
            current_time = datetime.now()
        
        if (current_time - self.last_cleanup).total_seconds() < 3600:
            return
        
        cutoff = current_time - timedelta(hours=24)
        
        for ip in list(self.failed_logins.keys()):
            self.failed_logins[ip] = [
                item for item in self.failed_logins[ip]
                if item['timestamp'] > cutoff
            ]
            if not self.failed_logins[ip]:
                del self.failed_logins[ip]
        
        for ip in list(self.targeted_users.keys()):
            for user in list(self.targeted_users[ip].keys()):
                self.targeted_users[ip][user] = [
                    item for item in self.targeted_users[ip][user]
                    if item['timestamp'] > cutoff
                ]
                if not self.targeted_users[ip][user]:
                    del self.targeted_users[ip][user]
            if not self.targeted_users[ip]:
                del self.targeted_users[ip]
        
        self.event_counts = [
            entry for entry in self.event_counts
            if entry['minute'] > cutoff
        ]
        
        for key in list(self.alert_history.keys()):
            if (current_time - self.alert_history[key]).total_seconds() > 86400:
                del self.alert_history[key]
        
        self.last_cleanup = current_time

"""Detection engine coordinating security rules."""

from typing import List, Dict, Any, Optional, Callable
from .rules import (
    DetectionRule,
    DetectionContext,
    BruteForceSSHRule,
    MultipleAccountsRule,
    SuspiciousRootLoginRule,
    SensitiveFileModificationRule,
    ActivitySpikeRule
)


class DetectionEngine:
    """Main detection engine for security anomalies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.context = DetectionContext()
        self.rules: List[DetectionRule] = []
        self.alert_callbacks: List[Callable] = []
        
        self._initialize_rules()
    
    def _initialize_rules(self):
        detection_config = self.config.get('detection', {})
        
        if 'bruteforce_ssh' in detection_config:
            self.rules.append(BruteForceSSHRule(detection_config['bruteforce_ssh']))
        
        if 'multiple_accounts' in detection_config:
            self.rules.append(MultipleAccountsRule(detection_config['multiple_accounts']))
        
        if 'suspicious_root_login' in detection_config:
            self.rules.append(SuspiciousRootLoginRule(detection_config['suspicious_root_login']))
        
        if 'sensitive_file_modification' in detection_config:
            self.rules.append(SensitiveFileModificationRule(detection_config['sensitive_file_modification']))
        
        if 'activity_spike' in detection_config:
            self.rules.append(ActivitySpikeRule(detection_config['activity_spike']))
    
    def register_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.alert_callbacks.append(callback)
    
    def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts = []
        
        for rule in self.rules:
            try:
                alert = rule.check(event, self.context)
                if alert:
                    alerts.append(alert)
                    for callback in self.alert_callbacks:
                        try:
                            callback(alert)
                        except Exception as e:
                            print(f"Alert callback error: {e}")
            except Exception as e:
                print(f"Rule {rule.name} error: {e}")
        
        return alerts
    
    def process_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        all_alerts = []
        
        for event in events:
            alerts = self.process_event(event)
            all_alerts.extend(alerts)
        
        return all_alerts
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for rule in self.rules if rule.enabled),
            'rules': [
                {
                    'name': rule.name,
                    'enabled': rule.enabled,
                    'severity': rule.severity
                }
                for rule in self.rules
            ],
            'context': {
                'tracked_ips': len(self.context.failed_logins),
                'event_history_size': len(self.context.event_counts)
            }
        }
    
    def reset_context(self):
        self.context = DetectionContext()

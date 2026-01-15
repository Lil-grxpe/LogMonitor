"""
Module du moteur de détection (F2)
Responsable : Sophie HOUNTONDJI

Ce module orchestre l'application des règles de détection
"""

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
    """Moteur principal de détection d'anomalies"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le moteur de détection
        
        Args:
            config: Configuration des règles
        """
        self.config = config
        self.context = DetectionContext()
        self.rules: List[DetectionRule] = []
        self.alert_callbacks: List[Callable] = []
        
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialise toutes les règles depuis la configuration"""
        detection_config = self.config.get('detection', {})
        
        # Règle 1 : Bruteforce SSH
        if 'bruteforce_ssh' in detection_config:
            self.rules.append(BruteForceSSHRule(detection_config['bruteforce_ssh']))
        
        # Règle 2 : Multiple accounts
        if 'multiple_accounts' in detection_config:
            self.rules.append(MultipleAccountsRule(detection_config['multiple_accounts']))
        
        # Règle 3 : Suspicious root login
        if 'suspicious_root_login' in detection_config:
            self.rules.append(SuspiciousRootLoginRule(detection_config['suspicious_root_login']))
        
        # Règle 4 : Sensitive file modification
        if 'sensitive_file_modification' in detection_config:
            self.rules.append(SensitiveFileModificationRule(detection_config['sensitive_file_modification']))
        
        # Règle 5 : Activity spike
        if 'activity_spike' in detection_config:
            self.rules.append(ActivitySpikeRule(detection_config['activity_spike']))
    
    def register_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Enregistre un callback à appeler quand une alerte est générée
        
        Args:
            callback: Fonction qui sera appelée avec l'alerte en paramètre
        """
        self.alert_callbacks.append(callback)
    
    def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Traite un événement normalisé avec toutes les règles
        
        Args:
            event: Événement normalisé à analyser
        
        Returns:
            Liste des alertes générées
        """
        alerts = []
        
        for rule in self.rules:
            try:
                alert = rule.check(event, self.context)
                if alert:
                    alerts.append(alert)
                    # Notifier les callbacks
                    for callback in self.alert_callbacks:
                        try:
                            callback(alert)
                        except Exception as e:
                            print(f"Erreur dans callback d'alerte: {e}")
            except Exception as e:
                print(f"Erreur lors de l'exécution de la règle {rule.name}: {e}")
        
        return alerts
    
    def process_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Traite un lot d'événements
        
        Args:
            events: Liste d'événements normalisés
        
        Returns:
            Liste de toutes les alertes générées
        """
        all_alerts = []
        
        for event in events:
            alerts = self.process_event(event)
            all_alerts.extend(alerts)
        
        return all_alerts
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Récupère des statistiques sur le moteur de détection
        
        Returns:
            Dict contenant les statistiques
        """
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
        """Réinitialise le contexte de détection"""
        self.context = DetectionContext()

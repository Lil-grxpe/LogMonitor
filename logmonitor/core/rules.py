"""
Module de règles de détection (F2)
Responsable : Sophie HOUNTONDJI

Ce module définit les 5 règles de détection d'anomalies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import dateutil.parser


class DetectionRule(ABC):
    """Classe abstraite de base pour toutes les règles de détection"""
    
    def __init__(self, name: str, severity: str, config: Dict[str, Any]):
        """
        Initialise une règle de détection
        
        Args:
            name: Nom de la règle
            severity: Niveau de sévérité (low, medium, high, critical)
            config: Configuration spécifique à la règle
        """
        self.name = name
        self.severity = severity
        self.config = config
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        """
        Vérifie si l'événement déclenche la règle
        
        Args:
            event: Événement normalisé à vérifier
            context: Contexte de détection (historique, état)
        
        Returns:
            Dict contenant l'alerte si détection, None sinon
        """
        pass
    
    def _create_alert(self, event: Dict[str, Any], description: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un dictionnaire d'alerte
        
        Args:
            event: Événement ayant déclenché l'alerte
            description: Description de l'alerte
            evidence: Preuves associées
        
        Returns:
            Dict représentant l'alerte
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'rule_name': self.name,
            'severity': self.severity,
            'description': description,
            'event': event,
            'evidence': evidence
        }


class BruteForceSSHRule(DetectionRule):
    """Règle 1 : Détection de bruteforce SSH"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('BruteForce SSH', config.get('severity', 'high'), config)
        self.threshold = config.get('threshold', 5)
        self.time_window = config.get('time_window', 300)  # secondes
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        """Vérifie les tentatives de bruteforce SSH"""
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'ssh_failed_login':
            return None
        
        source_ip = event.get('source_ip')
        if not source_ip:
            return None
        
        # Ajouter l'événement à l'historique
        context.add_failed_login(source_ip, event)
        
        # Obtenir le temps de l'événement courant
        current_time = context._get_event_time(event)
        
        # Vérifier le nombre d'échecs dans la fenêtre de temps
        recent_failures = context.get_recent_failed_logins(source_ip, self.time_window, current_time)
        
        if len(recent_failures) >= self.threshold:
            # Vérifier cooldown pour éviter le spam
            if context.should_alert(f"bruteforce_{source_ip}", self.time_window, current_time):
                return self._create_alert(
                    event,
                    f"Bruteforce SSH détecté: {len(recent_failures)} échecs de connexion depuis {source_ip} en {self.time_window}s",
                    {
                        'source_ip': source_ip,
                        'failed_attempts': len(recent_failures),
                        'time_window': self.time_window,
                        'attempts_details': recent_failures[-5:]  # Dernières 5 tentatives
                    }
                )
        
        return None


class MultipleAccountsRule(DetectionRule):
    """Règle 2 : Tentatives de connexion sur plusieurs comptes"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Multiple Accounts Attack', config.get('severity', 'medium'), config)
        self.threshold = config.get('threshold', 3)
        self.time_window = config.get('time_window', 600)  # secondes
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        """Vérifie les tentatives sur plusieurs comptes"""
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'ssh_failed_login':
            return None
        
        source_ip = event.get('source_ip')
        user = event.get('user')
        if not source_ip or not user:
            return None
        
        # Ajouter l'utilisateur ciblé
        context.add_targeted_user(source_ip, user, event)
        
        # Obtenir le temps de l'événement courant
        current_time = context._get_event_time(event)
        
        # Vérifier le nombre de comptes différents ciblés
        targeted_users = context.get_recent_targeted_users(source_ip, self.time_window, current_time)
        
        if len(targeted_users) >= self.threshold:
            # Vérifier cooldown pour éviter le spam
            if context.should_alert(f"multiple_accounts_{source_ip}", self.time_window, current_time):
                return self._create_alert(
                    event,
                    f"Tentatives sur plusieurs comptes: {len(targeted_users)} comptes ciblés depuis {source_ip}",
                    {
                        'source_ip': source_ip,
                        'targeted_accounts': list(targeted_users.keys()),
                        'total_attempts': sum(len(attempts) for attempts in targeted_users.values())
                    }
                )
        
        return None


class SuspiciousRootLoginRule(DetectionRule):
    """Règle 3 : Connexions root interactives suspectes"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Suspicious Root Login', config.get('severity', 'high'), config)
        self.allowed_sources = set(config.get('allowed_sources', []))
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        """Vérifie les connexions root suspectes"""
        if not self.enabled:
            return None
        
        if event.get('event_type') != 'ssh_accepted_login':
            return None
        
        user = event.get('user')
        source_ip = event.get('source_ip')
        
        if user != 'root':
            return None
        
        # Si des IPs autorisées sont définies et l'IP est dans la liste, OK
        if self.allowed_sources and source_ip in self.allowed_sources:
            return None
        
        # Obtenir le temps de l'événement courant
        current_time = context._get_event_time(event)
        
        # Vérifier cooldown
        if context.should_alert(f"root_login_{source_ip}", 3600, current_time):
             return self._create_alert(
                event,
                f"Connexion root suspecte depuis {source_ip}",
                {
                    'user': user,
                    'source_ip': source_ip,
                    'hostname': event.get('hostname'),
                    'allowed_sources': list(self.allowed_sources) if self.allowed_sources else "none"
                }
            )
        
        return None


class SensitiveFileModificationRule(DetectionRule):
    """Règle 4 : Modification de fichiers sensibles"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Sensitive File Modification', config.get('severity', 'critical'), config)
        self.watched_files = set(config.get('watched_files', [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/sudoers',
            '/etc/ssh/sshd_config'
        ]))
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        """Vérifie les modifications de fichiers sensibles"""
        if not self.enabled:
            return None
        
        # Combiner message et command pour la recherche
        message = (event.get('message', '') + ' ' + event.get('command', '')).lower()
        
        keywords = ['edit', 'modif', 'change', 'write', 'alter', 'update', 'vim', 'nano', 'vi', 'emacs']
        
        for watched_file in self.watched_files:
            if watched_file.lower() in message:
                if any(keyword in message for keyword in keywords):
                    return self._create_alert(
                        event,
                        f"Modification/Accès détecté sur fichier sensible: {watched_file}",
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
    """Règle 5 : Pics d'activité inhabituels"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('Activity Spike', config.get('severity', 'medium'), config)
        self.threshold_multiplier = config.get('threshold_multiplier', 3.0)
        self.baseline_window = config.get('baseline_window', 3600)  # secondes
    
    def check(self, event: Dict[str, Any], context: 'DetectionContext') -> Optional[Dict[str, Any]]:
        """Vérifie les pics d'activité"""
        if not self.enabled:
            return None
        
        # Compter les événements récents
        context.add_event_count(event)
        
        # Obtenir le temps de l'événement courant
        current_time = context._get_event_time(event)
        
        # Calculer la moyenne et détecter les pics
        recent_counts = context.get_event_counts(self.baseline_window, current_time)
        
        if len(recent_counts) < 10:  # Pas assez de données pour baseline
            return None
        
        # Prendre les 9 premières périodes pour baseline
        baseline = recent_counts[:-1]
        current = recent_counts[-1]
        
        if not baseline:
            return None
        
        avg_baseline = statistics.mean(baseline)
        
        if avg_baseline > 0 and current >= (avg_baseline * self.threshold_multiplier):
             # Vérifier cooldown
            if context.should_alert("activity_spike", 600, current_time):
                return self._create_alert(
                    event,
                    f"Pic d'activité détecté: {current} événements (moyenne: {avg_baseline:.1f})",
                    {
                        'current_rate': current,
                        'baseline_average': avg_baseline,
                        'multiplier': current / avg_baseline if avg_baseline > 0 else 0,
                        'threshold': self.threshold_multiplier
                    }
                )
        
        return None


class DetectionContext:
    """Contexte partagé pour toutes les règles de détection"""
    
    def __init__(self):
        # Historique des échecs de connexion par IP
        self.failed_logins: Dict[str, List[Dict]] = defaultdict(list)
        
        # Historique des utilisateurs ciblés par IP
        self.targeted_users: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        
        # Compteur d'événements pour détecter les pics
        self.event_counts: List[Dict[str, Any]] = []
        
        # Historique des alertes pour éviter le spam (cooldown)
        self.alert_history: Dict[str, datetime] = {}
        
        # Dernier nettoyage du contexte
        self.last_cleanup = datetime.now()

    def _get_event_time(self, event: Dict[str, Any]) -> datetime:
        """Extrait et convertit le timestamp de l'événement"""
        ts = event.get('timestamp')
        if isinstance(ts, datetime):
            return ts
        try:
            # Essayer de parser le format ISO standard
            return datetime.fromisoformat(str(ts))
        except (ValueError, TypeError):
            try:
                # Fallback pour d'autres formats si nécessaire, ou retourner maintenant
                # Mais pour le batch processing, il vaut mieux essayer de parser même "Jan 02 10:15:01" 
                # si c'était stocké tel quel.
                # Cependant, le normalizer convertit déjà en ISO string.
                # Si ça échoue, on utilise 'now', mais ça cassera le batch processing.
                return datetime.now()
            except:
                return datetime.now()

    def add_failed_login(self, source_ip: str, event: Dict[str, Any]):
        """Ajoute un échec de connexion"""
        event_time = self._get_event_time(event)
        self.failed_logins[source_ip].append({
            'timestamp': event_time,
            'event': event
        })
        self._cleanup_if_needed(event_time)
    
    def get_recent_failed_logins(self, source_ip: str, time_window: int, current_time: datetime = None) -> List[Dict]:
        """Récupère les échecs récents pour une IP"""
        if current_time is None:
            current_time = datetime.now()
            
        cutoff = current_time - timedelta(seconds=time_window)
        return [
            item for item in self.failed_logins[source_ip]
            if item['timestamp'] > cutoff
        ]
    
    def add_targeted_user(self, source_ip: str, user: str, event: Dict[str, Any]):
        """Ajoute un utilisateur ciblé"""
        event_time = self._get_event_time(event)
        self.targeted_users[source_ip][user].append({
            'timestamp': event_time,
            'event': event
        })
        self._cleanup_if_needed(event_time)
    
    def get_recent_targeted_users(self, source_ip: str, time_window: int, current_time: datetime = None) -> Dict[str, List]:
        """Récupère les utilisateurs ciblés récemment"""
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
        """Ajoute un événement au compteur"""
        event_time = self._get_event_time(event)
        
        # Ajouter ou incrémenter le compteur pour la minute courante
        current_minute = event_time.replace(second=0, microsecond=0)
        
        # Chercher l'entrée pour cette minute
        for entry in self.event_counts:
            if entry['minute'] == current_minute:
                entry['count'] += 1
                return
        
        # Nouvelle entrée
        self.event_counts.append({
            'minute': current_minute,
            'count': 1
        })
    
    def get_event_counts(self, time_window: int, current_time: datetime = None) -> List[int]:
        """Récupère les compteurs d'événements"""
        if current_time is None:
            current_time = datetime.now()
            
        cutoff = current_time - timedelta(seconds=time_window)
        
        # Filtrer et trier
        relevant_counts = [
            entry for entry in self.event_counts
            if entry['minute'] > cutoff and entry['minute'] <= current_time
        ]
        relevant_counts.sort(key=lambda x: x['minute'])
        
        return [entry['count'] for entry in relevant_counts]
        
    def should_alert(self, key: str, cooldown: int, current_time: datetime = None) -> bool:
        """
        Vérifie si une alerte doit être générée (gestion du cooldown)
        """
        if current_time is None:
            current_time = datetime.now()

        last_alert = self.alert_history.get(key)
        
        if last_alert is None or (current_time - last_alert).total_seconds() > cooldown:
            self.alert_history[key] = current_time
            return True
            
        return False
    
    def _cleanup_if_needed(self, current_time: datetime = None):
        """Nettoie les anciennes données du contexte"""
        if current_time is None:
            current_time = datetime.now()
        
        # Nettoyer toutes les heures
        if (current_time - self.last_cleanup).total_seconds() < 3600:
            return
        
        cutoff = current_time - timedelta(hours=24)  # Garder 24h d'historique
        
        # Nettoyer failed_logins
        for ip in list(self.failed_logins.keys()):
            self.failed_logins[ip] = [
                item for item in self.failed_logins[ip]
                if item['timestamp'] > cutoff
            ]
            if not self.failed_logins[ip]:
                del self.failed_logins[ip]
        
        # Nettoyer targeted_users
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
        
        # Nettoyer event_counts
        self.event_counts = [
            entry for entry in self.event_counts
            if entry['minute'] > cutoff
        ]
        
        # Nettoyer alert_history
        for key in list(self.alert_history.keys()):
            if (current_time - self.alert_history[key]).total_seconds() > 86400: # 24h retention
                del self.alert_history[key]
        
        self.last_cleanup = current_time

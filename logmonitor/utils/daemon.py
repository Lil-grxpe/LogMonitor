"""
Module de gestion du daemon LogMonitor
Permet l'exécution en arrière-plan avec surveillance continue

Ce module gère le processus daemon pour LogMonitor
"""

import os
import sys
import time
import signal
import atexit
from pathlib import Path
from typing import Optional
from datetime import datetime
import threading


class DaemonProcess:
    """Classe pour gérer le processus daemon de LogMonitor"""
    
    def __init__(self, pid_file: str, log_file: str = None):
        """
        Initialise le processus daemon
        
        Args:
            pid_file: Chemin vers le fichier PID
            log_file: Chemin vers le fichier de log (optionnel)
        """
        self.pid_file = Path(pid_file)
        self.log_file = Path(log_file) if log_file else None
        self.running = False
        
        # Créer les répertoires si nécessaire
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def daemonize(self):
        """
        Transforme le processus en daemon Unix
        Utilise le double fork
        """
        try:
            # Premier fork
            pid = os.fork()
            if pid > 0:
                # Parent process, quitter
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)
        
        # Détacher du terminal parent
        os.chdir('/')
        os.setsid()
        os.umask(0)
        
        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                # Parent process, quitter
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)
        
        # Rediriger les descripteurs de fichiers standards
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Rediriger stdin vers /dev/null
        with open('/dev/null', 'r') as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        
        # Rediriger stdout et stderr vers le fichier de log ou /dev/null
        if self.log_file:
            with open(self.log_file, 'a+') as f:
                os.dup2(f.fileno(), sys.stdout.fileno())
                os.dup2(f.fileno(), sys.stderr.fileno())
        else:
            with open('/dev/null', 'a+') as f:
                os.dup2(f.fileno(), sys.stdout.fileno())
                os.dup2(f.fileno(), sys.stderr.fileno())
        
        # Écrire le PID
        self._write_pid()
        
        # Enregistrer la fonction de nettoyage
        atexit.register(self._cleanup)
        
        # Gérer les signaux
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _write_pid(self):
        """Écrit le PID dans le fichier"""
        pid = str(os.getpid())
        with open(self.pid_file, 'w') as f:
            f.write(pid + '\n')
    
    def _cleanup(self):
        """Nettoie les fichiers temporaires"""
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        self.running = False
        self._cleanup()
        sys.exit(0)
    
    def get_pid(self) -> Optional[int]:
        """
        Récupère le PID depuis le fichier
        
        Returns:
            PID si le fichier existe, None sinon
        """
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, IOError):
            return None
    
    def is_running(self) -> bool:
        """
        Vérifie si le daemon est en cours d'exécution
        
        Returns:
            True si le daemon tourne, False sinon
        """
        pid = self.get_pid()
        if pid is None:
            return False
        
        # Vérifier si le processus existe
        try:
            os.kill(pid, 0)  # Signal 0 ne fait rien mais vérifie l'existence
            return True
        except OSError:
            return False
    
    def start(self, target_func, *args, **kwargs):
        """
        Démarre le daemon
        
        Args:
            target_func: Fonction à exécuter dans le daemon
            *args, **kwargs: Arguments pour la fonction
        """
        # Vérifier si déjà en cours
        if self.is_running():
            print("LogMonitor est déjà en cours d'exécution")
            sys.exit(1)
        
        # Supprimer le fichier PID obsolète
        if self.pid_file.exists():
            self.pid_file.unlink()
        
        # Se transformer en daemon
        self.daemonize()
        
        # Exécuter la fonction cible
        self.running = True
        target_func(*args, **kwargs)
    
    def stop(self):
        """Arrête le daemon"""
        pid = self.get_pid()
        
        if pid is None:
            print("LogMonitor n'est pas en cours d'exécution")
            return
        
        if not self.is_running():
            print("LogMonitor n'est pas en cours d'exécution (PID obsolète)")
            self._cleanup()
            return
        
        # Envoyer SIGTERM
        try:
            os.kill(pid, signal.SIGTERM)
            
            # Attendre que le processus se termine (max 10 secondes)
            for _ in range(100):
                if not self.is_running():
                    print("LogMonitor arrêté avec succès")
                    return
                time.sleep(0.1)
            
            # Si toujours en cours, forcer avec SIGKILL
            print("Arrêt forcé du processus...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
            
            if not self.is_running():
                print("LogMonitor arrêté (forcé)")
            else:
                print("Impossible d'arrêter LogMonitor")
                
        except OSError as e:
            print(f"Erreur lors de l'arrêt: {e}")
        finally:
            self._cleanup()
    
    def status(self) -> dict:
        """
        Retourne le statut du daemon
        
        Returns:
            Dictionnaire avec les informations de statut
        """
        pid = self.get_pid()
        running = self.is_running()
        
        status_info = {
            'running': running,
            'pid': pid if running else None,
            'pid_file': str(self.pid_file),
            'log_file': str(self.log_file) if self.log_file else None
        }
        
        return status_info


class LogMonitorDaemon:
    """Daemon principal de LogMonitor pour surveillance continue"""
    
    def __init__(self, config_manager):
        """
        Initialise le daemon LogMonitor
        
        Args:
            config_manager: Instance de ConfigManager
        """
        self.config = config_manager
        self.running = False
        
        # Importer les modules nécessaires
        from logmonitor.core.collector import create_collector
        from logmonitor.core.normalizer import create_normalizer
        from logmonitor.core.detector import DetectionEngine
        from logmonitor.storage.database import LogDatabase
        from logmonitor.storage.evidence import EvidenceManager
        from logmonitor.utils.logger import setup_logger
        
        # Initialiser les composants
        self.logger = setup_logger(
            'logmonitor.daemon',
            self.config.get('general.app_log', '/var/log/logmonitor/app.log'),
            self.config.get('general.log_level', 'INFO')
        )
        
        db_path = self.config.get('storage.database', 'data/logmonitor.db')
        self.db = LogDatabase(db_path)
        
        evidence_dir = self.config.get('storage.evidence_dir', 'data/evidence')
        self.evidence_manager = EvidenceManager(evidence_dir)
        
        self.detector = DetectionEngine(self.config.config)
        
        # Enregistrer le callback pour les alertes
        self.detector.register_alert_callback(self._handle_alert)
        
        # Créer les collecteurs pour chaque fichier de log
        self.collectors = {}
        self.normalizers = {}
        
        log_paths = self.config.get('logs.paths', [])
        for log_path in log_paths:
            try:
                collector = create_collector(log_path)
                normalizer = create_normalizer('auth' if 'auth' in log_path else 'syslog')
                self.collectors[log_path] = collector
                self.normalizers[log_path] = normalizer
            except Exception as e:
                self.logger.error(f"Impossible de créer le collecteur pour {log_path}: {e}")
        
        # Initialiser le processus daemon
        pid_file = self.config.get('general.pid_file', '/tmp/logmonitor/logmonitor.pid')
        log_file = self.config.get('general.app_log', '/tmp/logmonitor/app.log')
        self.daemon_process = DaemonProcess(pid_file, log_file)
    
    def get_pid(self):
        """Récupère le PID du daemon"""
        return self.daemon_process.get_pid()
    
    def is_running(self):
        """Vérifie si le daemon est en cours d'exécution"""
        return self.daemon_process.is_running()
    
    def start(self):
        """Démarre le daemon"""
        self.daemon_process.start(self.run)
    
    def stop(self):
        """Arrête le daemon"""
        self.daemon_process.stop()
    
    def _handle_alert(self, alert: dict):
        """
        Callback appelé quand une alerte est générée
        
        Args:
            alert: Dictionnaire contenant l'alerte
        """
        try:
            # Insérer dans la base de données
            alert_id = self.db.insert_alert(alert)
            
            # Stocker les preuves
            self.evidence_manager.store_evidence(alert_id, alert)
            
            # Logger l'alerte
            self.logger.warning(
                f"ALERTE [{alert['severity'].upper()}] {alert['rule_name']}: {alert['description']}"
            )
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de l'alerte: {e}")
    
    def _process_log_line(self, raw_line: str, log_path: str):
        """
        Traite une ligne de log
        
        Args:
            raw_line: Ligne brute
            log_path: Chemin du fichier de log
        """
        try:
            normalizer = self.normalizers[log_path]
            normalized = normalizer.normalize(raw_line)
            
            if normalized:
                # Stocker dans la DB
                self.db.insert_log(normalized)
                
                # Détecter anomalies
                self.detector.process_event(normalized)
                
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de la ligne: {e}")
    
    def run(self):
        """Boucle principale du daemon"""
        self.running = True
        self.logger.info("LogMonitor daemon démarré")
        
        # Utiliser le mode streaming pour chaque collecteur
        threads = []
        
        for log_path, collector in self.collectors.items():
            # Créer un thread pour chaque fichier de log
            callback = lambda line, path=log_path: self._process_log_line(line, path)
            thread = threading.Thread(
                target=collector.collect_streaming,
                args=(callback,),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            self.logger.info(f"Surveillance démarrée pour {log_path}")
        
        # Boucle principale - attendre les threads
        try:
            while self.running:
                time.sleep(1)
                
                # Vérifier que les threads sont toujours vivants
                for thread in threads:
                    if not thread.is_alive():
                        self.logger.warning("Un thread de surveillance est mort, redémarrage...")
                        # TODO: Redémarrer le thread
        
        except KeyboardInterrupt:
            self.logger.info("Arrêt demandé par l'utilisateur")
        finally:
            self.running = False
            self.db.close()
            self.logger.info("LogMonitor daemon arrêté")

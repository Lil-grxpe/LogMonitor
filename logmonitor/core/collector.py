"""
Module de collecte de logs (F1)
Responsable : Melkior AGUESSI

Ce module fournit des classes pour lire et collecter les logs
depuis différentes sources (auth.log, syslog, etc.)
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Iterator, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


class LogCollector(ABC):
    """Classe abstraite de base pour tous les collecteurs de logs"""
    
    def __init__(self, log_path: str):
        """
        Initialise le collecteur
        
        Args:
            log_path: Chemin vers le fichier de log
        """
        self.log_path = Path(log_path)
        self._validate_path()
    
    def _validate_path(self) -> None:
        """Vérifie que le fichier de log existe et est lisible"""
        if not self.log_path.exists():
            raise FileNotFoundError(f"Le fichier {self.log_path} n'existe pas")
        if not os.access(self.log_path, os.R_OK):
            raise PermissionError(f"Pas de permission de lecture pour {self.log_path}")
    
    @abstractmethod
    def collect_batch(self) -> Iterator[str]:
        """
        Collecte toutes les lignes du fichier (mode batch)
        
        Yields:
            str: Une ligne de log brute
        """
        pass
    
    def collect_streaming(self, callback) -> None:
        """
        Surveille le fichier et appelle le callback pour chaque nouvelle ligne
        
        Args:
            callback: Fonction à appeler avec chaque nouvelle ligne
        """
        # Implémentation de base utilisant watchdog
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
    """Gestionnaire d'événements pour surveiller les modifications de fichier"""
    
    def __init__(self, log_path: Path, callback):
        self.log_path = log_path
        self.callback = callback
        self.last_position = 0
        
        # Initialiser la position à la fin du fichier
        if self.log_path.exists():
            with open(self.log_path, 'r') as f:
                f.seek(0, os.SEEK_END)
                self.last_position = f.tell()
    
    def on_modified(self, event):
        """Appelé quand le fichier est modifié"""
        if isinstance(event, FileModifiedEvent) and Path(event.src_path) == self.log_path:
            self._read_new_lines()
    
    def _read_new_lines(self):
        """Lit les nouvelles lignes depuis la dernière position"""
        try:
            with open(self.log_path, 'r') as f:
                f.seek(self.last_position)
                for line in f:
                    if line.strip():  # Ignorer les lignes vides
                        self.callback(line.rstrip('\n'))
                self.last_position = f.tell()
        except Exception as e:
            # Log l'erreur mais continue la surveillance
            print(f"Erreur lors de la lecture: {e}")


class AuthLogCollector(LogCollector):
    """Collecteur spécialisé pour auth.log"""
    
    def collect_batch(self) -> Iterator[str]:
        """
        Collecte toutes les lignes de auth.log
        
        Yields:
            str: Une ligne de log brute
        """
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():  # Ignorer les lignes vides
                        yield line
        except Exception as e:
            raise IOError(f"Erreur lors de la lecture de {self.log_path}: {e}")


class SyslogCollector(LogCollector):
    """Collecteur spécialisé pour syslog"""
    
    def collect_batch(self) -> Iterator[str]:
        """
        Collecte toutes les lignes de syslog
        
        Yields:
            str: Une ligne de log brute
        """
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():  # Ignorer les lignes vides
                        yield line
        except Exception as e:
            raise IOError(f"Erreur lors de la lecture de {self.log_path}: {e}")


class GenericLogCollector(LogCollector):
    """Collecteur générique pour tout type de fichier log"""
    
    def collect_batch(self) -> Iterator[str]:
        """
        Collecte toutes les lignes du fichier
        
        Yields:
            str: Une ligne de log brute
        """
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():  # Ignorer les lignes vides
                        yield line
        except Exception as e:
            raise IOError(f"Erreur lors de la lecture de {self.log_path}: {e}")


def create_collector(log_path: str) -> LogCollector:
    """
    Factory function pour créer le bon type de collecteur
    
    Args:
        log_path: Chemin vers le fichier de log
    
    Returns:
        LogCollector: Instance appropriée du collecteur
    """
    path = Path(log_path)
    
    if 'auth.log' in path.name:
        return AuthLogCollector(log_path)
    elif 'syslog' in path.name:
        return SyslogCollector(log_path)
    else:
        return GenericLogCollector(log_path)

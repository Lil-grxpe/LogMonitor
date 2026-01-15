"""
Module de gestion de configuration (Utils)
Responsable : Consylia AIHOU

Ce module gère le chargement et la validation de la configuration YAML
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os


class ConfigManager:
    """Gestionnaire de configuration pour LogMonitor"""
    
    def __init__(self, config_path: str = None):
        """
        Initialise le gestionnaire de configuration
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        if config_path is None:
            # Chemins par défaut
            config_path = self._find_default_config()
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def _find_default_config(self) -> str:
        """Trouve le fichier de configuration par défaut"""
        # Chercher dans plusieurs emplacements
        locations = [
            Path('config/logmonitor.yaml'),
            Path('/etc/logmonitor/logmonitor.yaml'),
            Path.home() / '.config/logmonitor/logmonitor.yaml',
        ]
        
        for location in locations:
            if location.exists():
                return str(location)
        
        # Retourner le premier emplacement par défaut
        return str(locations[0])
    
    def load(self) -> Dict[str, Any]:
        """
        Charge la configuration depuis le fichier YAML
        
        Returns:
            Dictionnaire de configuration
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Fichier de configuration non trouvé: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Valider la configuration
        self.validate()
        
        # Étendre les chemins relatifs
        self._expand_paths()
        
        return self.config
    
    def validate(self) -> bool:
        """
        Valide la configuration
        
        Returns:
            True si la configuration est valide
        
        Raises:
            ValueError: Si la configuration est invalide
        """
        required_sections = ['logs', 'detection', 'storage']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Section requise manquante dans la configuration: {section}")
        
        # Valider la section logs
        if 'paths' not in self.config['logs']:
            raise ValueError("Configuration logs.paths requise")
        
        if not isinstance(self.config['logs']['paths'], list):
            raise ValueError("logs.paths doit être une liste")
        
        # Valider la section detection
        detection = self.config.get('detection', {})
        valid_rules = ['bruteforce_ssh', 'multiple_accounts', 'suspicious_root_login',
                      'sensitive_file_modification', 'activity_spike']
        
        for rule in valid_rules:
            if rule in detection and not isinstance(detection[rule], dict):
                raise ValueError(f"Configuration de la règle {rule} doit être un dictionnaire")
        
        # Valider la section storage
        if 'database' not in self.config['storage']:
            raise ValueError("Configuration storage.database requise")
        
        return True
    
    def _expand_paths(self):
        """Étend les chemins relatifs en chemins absolus"""
        # Étendre les chemins de logs
        if 'paths' in self.config.get('logs', {}):
            log_paths = self.config['logs']['paths']
            self.config['logs']['paths'] = [str(Path(path).expanduser().resolve()) for path in log_paths]
        
        # Étendre le chemin de la base de données
        if 'database' in self.config.get('storage', {}):
            db_path = self.config['storage']['database']
            self.config['storage']['database'] = str(Path(db_path).expanduser().resolve())
        
        # Étendre le répertoire de preuves
        if 'evidence_dir' in self.config.get('storage', {}):
            evidence_path = self.config['storage']['evidence_dir']
            self.config['storage']['evidence_dir'] = str(Path(evidence_path).expanduser().resolve())
        
        # Étendre le répertoire de rapports
        if 'output_dir' in self.config.get('reporting', {}):
            report_path = self.config['reporting']['output_dir']
            self.config['reporting']['output_dir'] = str(Path(report_path).expanduser().resolve())

        # Étendre les chemins general
        if 'general' in self.config:
            if 'pid_file' in self.config['general']:
                self.config['general']['pid_file'] = str(Path(self.config['general']['pid_file']).expanduser().resolve())
            if 'app_log' in self.config['general']:
                self.config['general']['app_log'] = str(Path(self.config['general']['app_log']).expanduser().resolve())
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration
        
        Args:
            key: Clé en notation pointée (ex: 'detection.bruteforce_ssh.threshold')
            default: Valeur par défaut si la clé n'existe pas
        
        Returns:
            Valeur de configuration
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self, path: Optional[str] = None):
        """
        Sauvegarde la configuration dans un fichier
        
        Args:
            path: Chemin de sauvegarde (optionnel, utilise self.config_path par défaut)
        """
        save_path = Path(path) if path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)


# Instance singleton
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Récupère l'instance singleton du gestionnaire de configuration
    
    Args:
        config_path: Chemin vers le fichier de configuration (optionnel)
    
    Returns:
        Instance de ConfigManager
    """
    global _config_instance
    
    if _config_instance is None or config_path is not None:
        _config_instance = ConfigManager(config_path)
    
    return _config_instance

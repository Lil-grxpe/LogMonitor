"""Configuration manager for YAML config files."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os


class ConfigManager:
    """Configuration manager for LogMonitor."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = self._find_default_config()
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def _find_default_config(self) -> str:
        locations = [
            Path('config/logmonitor.yaml'),
            Path('/etc/logmonitor/logmonitor.yaml'),
            Path.home() / '.config/logmonitor/logmonitor.yaml',
        ]
        
        for location in locations:
            if location.exists():
                return str(location)
        
        return str(locations[0])
    
    def load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.validate()
        self._expand_paths()
        
        return self.config
    
    def validate(self) -> bool:
        required_sections = ['logs', 'detection', 'storage']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
        
        if 'paths' not in self.config['logs']:
            raise ValueError("logs.paths is required")
        
        if not isinstance(self.config['logs']['paths'], list):
            raise ValueError("logs.paths must be a list")
        
        detection = self.config.get('detection', {})
        valid_rules = ['bruteforce_ssh', 'multiple_accounts', 'suspicious_root_login',
                      'sensitive_file_modification', 'activity_spike']
        
        for rule in valid_rules:
            if rule in detection and not isinstance(detection[rule], dict):
                raise ValueError(f"Rule config {rule} must be a dict")
        
        if 'database' not in self.config['storage']:
            raise ValueError("storage.database is required")
        
        return True
    
    def _expand_paths(self):
        """Expand relative paths and auto-detect log paths if needed."""
        from logmonitor.utils.linux_detect import find_existing_log_paths, detect_distro, uses_journald

        if 'paths' in self.config.get('logs', {}):
            auto_detect = self.config.get('logs', {}).get('auto_detect', True)

            if auto_detect:
                # Always detect real system log paths first, regardless of configured paths
                distro = detect_distro()
                detected_paths = find_existing_log_paths(distro)
                self.config['logs']['_detected_distro'] = distro

                if detected_paths:
                    # Merge: system paths first, then any other existing configured paths
                    # (excluding test/relative paths that are not system logs)
                    configured_paths = self.config['logs']['paths']
                    extra_paths = []
                    for path in configured_paths:
                        p = Path(path).expanduser().resolve()
                        # Only keep configured paths that are absolute system paths
                        if p.exists() and str(p).startswith('/var/log'):
                            if str(p) not in detected_paths:
                                extra_paths.append(str(p))
                    self.config['logs']['paths'] = detected_paths + extra_paths
                elif uses_journald(distro):
                    self.config['logs']['_uses_journald'] = True
                # auto_detect disabled: only keep configured paths that actually exist or are virtual
                configured_paths = self.config['logs']['paths']
                existing_paths = []
                for path in configured_paths:
                    if path.startswith('journald://'):
                        existing_paths.append(path)
                    else:
                        p = Path(path).expanduser().resolve()
                        if p.exists():
                            existing_paths.append(str(p))
                if existing_paths:
                    self.config['logs']['paths'] = existing_paths
        
        if 'paths' in self.config.get('logs', {}):
            log_paths = self.config['logs']['paths']
            resolved_paths = []
            for path in log_paths:
                if path.startswith('journald://'):
                    resolved_paths.append(path)
                else:
                    resolved_paths.append(str(Path(path).expanduser().resolve()))
            self.config['logs']['paths'] = resolved_paths
        
        if 'database' in self.config.get('storage', {}):
            db_path = self.config['storage']['database']
            self.config['storage']['database'] = str(Path(db_path).expanduser().resolve())
        
        if 'evidence_dir' in self.config.get('storage', {}):
            evidence_path = self.config['storage']['evidence_dir']
            self.config['storage']['evidence_dir'] = str(Path(evidence_path).expanduser().resolve())
        
        if 'output_dir' in self.config.get('reporting', {}):
            report_path = self.config['reporting']['output_dir']
            self.config['reporting']['output_dir'] = str(Path(report_path).expanduser().resolve())

        if 'general' in self.config:
            if 'pid_file' in self.config['general']:
                self.config['general']['pid_file'] = str(Path(self.config['general']['pid_file']).expanduser().resolve())
            if 'app_log' in self.config['general']:
                self.config['general']['app_log'] = str(Path(self.config['general']['app_log']).expanduser().resolve())
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self, path: Optional[str] = None):
        save_path = Path(path) if path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)


_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    global _config_instance
    
    if _config_instance is None or config_path is not None:
        _config_instance = ConfigManager(config_path)
    
    return _config_instance

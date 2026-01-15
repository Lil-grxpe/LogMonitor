"""
Module de gestion des preuves (F3)
Responsable : Darwin BATONON

Ce module gère le stockage et l'intégrité des preuves
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class EvidenceManager:
    """Gestionnaire de preuves pour les alertes"""
    
    def __init__(self, evidence_dir: str):
        """
        Initialise le gestionnaire de preuves
        
        Args:
            evidence_dir: Répertoire de stockage des preuves
        """
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def store_evidence(self, alert_id: int, alert_data: Dict[str, Any]) -> str:
        """
        Stocke les preuves d'une alerte
        
        Args:
            alert_id: ID de l'alerte
            alert_data: Données de l'alerte
        
        Returns:
            Hash SHA256 des preuves
        """
        # Créer un sous-répertoire par date
        today = datetime.now().strftime("%Y%m%d")
        day_dir = self.evidence_dir / today
        day_dir.mkdir(exist_ok=True)
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"alert_{alert_id}_{timestamp}.json"
        filepath = day_dir / filename
        
        # Préparer les données
        evidence = {
            'alert_id': alert_id,
            'timestamp': datetime.now().isoformat(),
            'alert_data': alert_data
        }
        
        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2, ensure_ascii=False)
        
        # Calculer le hash
        file_hash = self._calculate_hash(filepath)
        
        # Sauvegarder le hash dans un fichier séparé
        hash_file = filepath.with_suffix('.hash')
        with open(hash_file, 'w') as f:
            f.write(file_hash)
        
        return file_hash
    
    def verify_evidence(self, filepath: str) -> bool:
        """
        Vérifie l'intégrité d'un fichier de preuve
        
        Args:
            filepath: Chemin vers le fichier de preuve
        
        Returns:
            True si l'intégrité est valide
        """
        filepath = Path(filepath)
        hash_file = filepath.with_suffix('.hash')
        
        if not hash_file.exists():
            return False
        
        # Lire le hash stocké
        with open(hash_file, 'r') as f:
            stored_hash = f.read().strip()
        
        # Calculer le hash actuel
        current_hash = self._calculate_hash(filepath)
        
        return stored_hash == current_hash
    
    def get_evidence_for_alert(self, alert_id: int) -> List[Path]:
        """
        Récupère tous les fichiers de preuves pour une alerte
        
        Args:
            alert_id: ID de l'alerte
        
        Returns:
            Liste des chemins de fichiers
        """
        pattern = f"alert_{alert_id}_*.json"
        return list(self.evidence_dir.rglob(pattern))
    
    def _calculate_hash(self, filepath: Path) -> str:
        """
        Calcule le hash SHA256 d'un fichier
        
        Args:
            filepath: Chemin vers le fichier
        
        Returns:
            Hash en hexadécimal
        """
        sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def export_evidence(self, alert_id: int, output_path: str):
        """
        Exporte toutes les preuves d'une alerte dans un fichier
        
        Args:
            alert_id: ID de l'alerte
            output_path: Chemin de sortie
        """
        evidence_files = self.get_evidence_for_alert(alert_id)
        
        if not evidence_files:
            raise ValueError(f"Aucune preuve trouvée pour l'alerte {alert_id}")
        
        # Combiner toutes les preuves
        all_evidence = []
        for filepath in evidence_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                all_evidence.append(json.load(f))
        
        # Exporter
        output = Path(output_path)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump({
                'alert_id': alert_id,
                'export_date': datetime.now().isoformat(),
                'evidence_count': len(all_evidence),
                'evidence': all_evidence
            }, f, indent=2, ensure_ascii=False)

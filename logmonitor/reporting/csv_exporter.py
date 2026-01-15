"""
Module d'export CSV (F4)
Responsable : Camel DADAVI

Ce module exporte les données en format CSV
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json


class CSVExporter:
    """Exporteur de données en format CSV"""
    
    def __init__(self, output_dir: str):
        """
        Initialise l'exporteur CSV
        
        Args:
            output_dir: Répertoire de sortie
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_alerts(self, alerts: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Exporte les alertes en CSV
        
        Args:
            alerts: Liste des alertes
            filename: Nom du fichier (optionnel)
        
        Returns:
            Chemin vers le fichier CSV
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alerts_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        if not alerts:
            # Créer un fichier vide avec headers
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'rule_name', 'severity', 'description'])
            return str(filepath)
        
        # Déterminer toutes les clés possibles
        fieldnames = set()
        for alert in alerts:
            fieldnames.update(alert.keys())
        fieldnames = sorted(fieldnames)
        
        # Écrire le CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for alert in alerts:
                # Convertir les objets complexes en JSON strings
                row = {}
                for key, value in alert.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                writer.writerow(row)
        
        return str(filepath)
    
    def export_logs(self, logs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Exporte les logs en CSV
        
        Args:
            logs: Liste des logs
            filename: Nom du fichier (optionnel)
        
        Returns:
            Chemin vers le fichier CSV
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        if not logs:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'hostname', 'service', 'level', 'message'])
            return str(filepath)
        
        fieldnames = set()
        for log in logs:
            fieldnames.update(log.keys())
        fieldnames = sorted(fieldnames)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in logs:
                row = {}
                for key, value in log.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                writer.writerow(row)
        
        return str(filepath)
    
    def export_statistics(self, statistics: Dict[str, Any], filename: str = None) -> str:
        """
        Exporte les statistiques en CSV
        
        Args:
            statistics: Dictionnaire de statistiques
            filename: Nom du fichier (optionnel)
        
        Returns:
            Chemin vers le fichier CSV
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"statistics_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            
            for key, value in statistics.items():
                if isinstance(value, dict):
                    # Métriques imbriquées
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"{key}.{sub_key}", sub_value])
                elif isinstance(value, list):
                    writer.writerow([key, json.dumps(value, ensure_ascii=False)])
                else:
                    writer.writerow([key, value])
        
        return str(filepath)

"""
Module de génération unifiée de rapports
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from logmonitor.storage.database import LogDatabase
from logmonitor.reporting.pdf_generator import PDFReportGenerator
from logmonitor.reporting.csv_exporter import CSVExporter
import json

class ReportGenerator:
    """Générateur principal de rapports (Façade)"""
    
    def __init__(self, config):
        """
        Initialise le générateur
        
        Args:
            config: Configuration de l'application
        """
        self.config = config
        self.db_path = config.get('storage.database', 'data/logmonitor.db')
        
    def generate_report(self, output_file: str, report_format: str = 'pdf') -> str:
        """
        Génère un rapport dans le format demandé
        
        Args:
            output_file: Chemin du fichier de sortie
            report_format: Format du rapport ('pdf' ou 'csv')
            
        Returns:
            Chemin vers le fichier généré
        """
        # Récupérer les données depuis la base de données
        db = LogDatabase(self.db_path)
        try:
            alerts = db.get_recent_alerts(limit=1000) # Récupérer un nombre suffisant d'alertes
            stats = db.get_statistics()
        finally:
            db.close()
            
        output_path = Path(output_file)
        output_dir = output_path.parent
        
        # S'assurer que le répertoire existe
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            
        if report_format.lower() == 'pdf':
            generator = PDFReportGenerator(str(output_dir))
            # Note: PDFReportGenerator.generate_report retourne le path, mais sa signature est différente
            # Elle attend (alerts, statistics, period) et ne prend pas de nom de fichier de sortie direct
            # On va devoir adapter ou renommer après
            
            # Hack: on génère le rapport puis on le renomme si nécessaire
            # Mais PDFReportGenerator.generate_report utilise un nom par défaut
            # On va essayer de voir si on peut forcer le nom ou juste renommer
            generated_path = generator.generate_report(alerts, stats)
            
            if output_path.name != Path(generated_path).name:
                # Renommer/Déplacer
                if output_path.exists():
                    os.unlink(output_path)
                os.rename(generated_path, output_path)
                return str(output_path)
            return generated_path
            
        elif report_format.lower() == 'csv':
            exporter = CSVExporter(str(output_dir))
            # Pour CSV, on a 3 types d'export possibles. 
            # Le CLI semble vouloir un seul rapport. On va exporter les alertes par défaut.
            return exporter.export_alerts(alerts, filename=output_path.name)
            
        else:
            raise ValueError(f"Format de rapport non supporté: {report_format}")

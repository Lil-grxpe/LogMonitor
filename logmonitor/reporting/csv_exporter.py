"""CSV export functionality."""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class CSVExporter:
    """CSV data exporter."""
    
    def export_alerts(self, output_file: str, alerts: List[Dict]):
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not alerts:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                f.write("No alerts to export\n")
            return
        
        all_fields = set()
        for alert in alerts:
            all_fields.update(alert.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for alert in alerts:
                row = {}
                for key, value in alert.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, default=str)
                    else:
                        row[key] = value
                writer.writerow(row)
    
    def export_logs(self, output_file: str, logs: List[Dict]):
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not logs:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                f.write("No logs to export\n")
            return
        
        all_fields = set()
        for log in logs:
            all_fields.update(log.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for log in logs:
                row = {}
                for key, value in log.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, default=str)
                    else:
                        row[key] = value
                writer.writerow(row)
    
    def export_statistics(self, output_file: str, statistics: Dict[str, Any]):
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            
            for key, value in statistics.items():
                if isinstance(value, (dict, list)):
                    writer.writerow([key, json.dumps(value, default=str)])
                else:
                    writer.writerow([key, value])

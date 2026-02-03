"""Evidence management with SHA256 hash verification."""

import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class EvidenceManager:
    """Manager for digital evidence with hash sealing."""
    
    def __init__(self, evidence_dir: str):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def store_evidence(self, alert_id: int, alert_data: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y%m%d")
        day_dir = self.evidence_dir / today
        day_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"alert_{alert_id}_{timestamp}.json"
        filepath = day_dir / filename
        
        evidence = {
            'alert_id': alert_id,
            'timestamp': datetime.now().isoformat(),
            'alert_data': alert_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2, ensure_ascii=False)
        
        file_hash = self._calculate_hash(filepath)
        
        hash_file = filepath.with_suffix('.hash')
        with open(hash_file, 'w') as f:
            f.write(file_hash)
        
        return file_hash
    
    def verify_evidence(self, filepath: str) -> bool:
        filepath = Path(filepath)
        hash_file = filepath.with_suffix('.hash')
        
        if not hash_file.exists():
            return False
        
        with open(hash_file, 'r') as f:
            stored_hash = f.read().strip()
        
        current_hash = self._calculate_hash(filepath)
        
        return stored_hash == current_hash
    
    def get_evidence_for_alert(self, alert_id: int) -> List[Path]:
        pattern = f"alert_{alert_id}_*.json"
        return list(self.evidence_dir.rglob(pattern))
    
    def _calculate_hash(self, filepath: Path) -> str:
        sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def export_evidence(self, alert_id: int, output_path: str):
        evidence_files = self.get_evidence_for_alert(alert_id)
        
        if not evidence_files:
            raise ValueError(f"No evidence found for alert {alert_id}")
        
        all_evidence = []
        for filepath in evidence_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                all_evidence.append(json.load(f))
        
        output = Path(output_path)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump({
                'alert_id': alert_id,
                'export_date': datetime.now().isoformat(),
                'evidence_count': len(all_evidence),
                'evidence': all_evidence
            }, f, indent=2, ensure_ascii=False)

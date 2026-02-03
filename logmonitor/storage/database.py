"""SQLite database module for logs and alerts storage."""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class LogDatabase:
    """SQLite database interface for logs and alerts."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                hostname TEXT,
                service TEXT,
                level TEXT,
                message TEXT,
                event_type TEXT,
                user TEXT,
                source_ip TEXT,
                data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                acknowledged INTEGER DEFAULT 0,
                event_data TEXT,
                evidence_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_source_ip ON logs(source_ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)')
        
        self.conn.commit()
    
    def insert_log(self, log_event: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO logs (timestamp, hostname, service, level, message, 
                            event_type, user, source_ip, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_event.get('timestamp'),
            log_event.get('hostname'),
            log_event.get('service'),
            log_event.get('level'),
            log_event.get('message'),
            log_event.get('event_type'),
            log_event.get('user'),
            log_event.get('source_ip'),
            json.dumps(log_event, default=str)
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_alert(self, alert: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (timestamp, rule_name, severity, description,
                              event_data, evidence_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alert.get('timestamp'),
            alert.get('rule_name'),
            alert.get('severity'),
            alert.get('description'),
            json.dumps(alert.get('event', {}), default=str),
            alert.get('evidence_hash', '')
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def store_evidence(self, alert_id: int, alert_data: Dict[str, Any]) -> str:
        evidence_dir = self.db_path.parent / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"alert_{alert_id}_{timestamp_str}.json"
        filepath = evidence_dir / filename
        
        alert_json_data = json.dumps(alert_data, indent=4, default=str)
        file_hash = hashlib.sha256(alert_json_data.encode('utf-8')).hexdigest()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(alert_json_data)
            
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO evidence (alert_id, file_path, file_hash)
            VALUES (?, ?, ?)
        ''', (alert_id, str(filepath), file_hash))
        
        cursor.execute('''
            UPDATE alerts
            SET evidence_hash = ?
            WHERE id = ?
        ''', (file_hash, alert_id))
        
        self.conn.commit()
        return file_hash

    def verify_evidence(self, filepath: str) -> bool:
        filepath_obj = Path(filepath)
        if not filepath_obj.exists():
            return False

        with open(filepath_obj, 'r', encoding='utf-8') as f:
            current_data = f.read()
        
        current_hash = hashlib.sha256(current_data.encode('utf-8')).hexdigest()
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT file_hash FROM evidence WHERE file_path = ?', (filepath,))
        result = cursor.fetchone()
        
        if result:
            original_hash = result['file_hash']
            return current_hash == original_hash
        return False
    
    def get_recent_alerts(self, limit: int = 100, severity: Optional[str] = None) -> List[Dict]:
        cursor = self.conn.cursor()
        
        if severity:
            cursor.execute('''
                SELECT * FROM alerts 
                WHERE severity = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (severity, limit))
        else:
            cursor.execute('''
                SELECT * FROM alerts 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_alerts_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM alerts 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM logs')
        total_logs = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM alerts')
        total_alerts = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT severity, COUNT(*) as count 
            FROM alerts 
            GROUP BY severity
        ''')
        alerts_by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute('''
            SELECT source_ip, COUNT(*) as count
            FROM logs
            WHERE event_type = 'ssh_failed_login'
            GROUP BY source_ip
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_suspicious_ips = [dict(row) for row in cursor.fetchall()]
        
        return {
            'total_logs': total_logs,
            'total_alerts': total_alerts,
            'alerts_by_severity': alerts_by_severity,
            'top_suspicious_ips': top_suspicious_ips
        }
    
    def get_alerts_by_hour(self, hours: int = 24) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        # SQLite specific date manipulation
        cursor.execute('''
            SELECT strftime('%Y-%m-%d %H:00:00', timestamp) as hour, COUNT(*) as count
            FROM alerts
            WHERE timestamp >= datetime('now', ?)
            GROUP BY hour
            ORDER BY hour ASC
        ''', (f'-{hours} hours',))
        
        rows = cursor.fetchall()
        
        # Fill missing hours
        data = {row['hour']: row['count'] for row in rows}
        result_labels = []
        result_data = []
        
        current_hour = datetime.now()
        # Generate last 24h labels
        from datetime import timedelta
        for i in range(hours, -1, -1):
            t = current_hour - timedelta(hours=i)
            key = t.strftime('%Y-%m-%d %H:00:00')
            label = t.strftime('%H:00')
            
            # Find the closest matching key in data (SQLite might vary slightly)
            # Actually for simplicity let's just use the key if it matches exactly
            result_labels.append(label)
            result_data.append(data.get(key, 0))
            
        return {
            'labels': result_labels,
            'data': result_data
        }
    
    def acknowledge_alert(self, alert_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE alerts 
            SET status = 'acknowledged' 
            WHERE id = ?
        ''', (alert_id,))
        self.conn.commit()

    def clear_all(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM logs')
        cursor.execute('DELETE FROM alerts')
        self.conn.commit()
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

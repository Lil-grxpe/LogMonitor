"""
Module de gestion de base de données
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class LogDatabase:
    """Gestionnaire de base de données SQLite pour LogMonitor"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Établit la connexion à la base de données"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """Crée les tables si elles n'existent pas"""
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
                evidence_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER,
                file_hash TEXT,
                raw_logs TEXT,
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
        """Insère un événement de log"""
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
        """Insère une alerte"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (timestamp, rule_name, severity, description,
                              event_data, evidence_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alert.get('timestamp'),
            alert.get('rule_name'),
            alert.get('severity'),
            alert.get('description'),
            json.dumps(alert.get('event', {}), default=str),
            json.dumps(alert.get('evidence', {}), default=str)
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_recent_alerts(self, limit: int = 100, severity: Optional[str] = None) -> List[Dict]:
        """Récupère les alertes récentes"""
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
        """Récupère les alertes dans une plage de dates"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM alerts 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère des statistiques sur la base de données"""
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
    
    def acknowledge_alert(self, alert_id: int):
        """Marque une alerte comme acquittée"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE alerts 
            SET status = 'acknowledged' 
            WHERE id = ?
        ''', (alert_id,))
        self.conn.commit()

    def clear_all(self):
        """Supprime toutes les données (logs et alertes)"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM logs')
        cursor.execute('DELETE FROM alerts')
        self.conn.commit()
    
    def close(self):
        """Ferme la connexion"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

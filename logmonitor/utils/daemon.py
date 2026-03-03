"""Daemon process management with Unix double-fork."""

import os
import sys
import time
import signal
import atexit
from pathlib import Path
from typing import Optional
from datetime import datetime
import threading


class DaemonProcess:
    """Low-level daemon process manager."""
    
    def __init__(self, pid_file: str, log_file: str = None):
        self.pid_file = Path(pid_file)
        self.log_file = Path(log_file) if log_file else None
        self.running = False
        
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)
        
        os.chdir('/')
        os.setsid()
        os.umask(0)
        
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)
        
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open('/dev/null', 'r') as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        
        if self.log_file:
            with open(self.log_file, 'a+') as f:
                os.dup2(f.fileno(), sys.stdout.fileno())
                os.dup2(f.fileno(), sys.stderr.fileno())
        else:
            with open('/dev/null', 'a+') as f:
                os.dup2(f.fileno(), sys.stdout.fileno())
                os.dup2(f.fileno(), sys.stderr.fileno())
        
        self._write_pid()
        atexit.register(self._cleanup)
        
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _write_pid(self):
        pid = str(os.getpid())
        with open(self.pid_file, 'w') as f:
            f.write(pid + '\n')
    
    def _cleanup(self):
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def _signal_handler(self, signum, frame):
        self.running = False
        self._cleanup()
        sys.exit(0)
    
    def get_pid(self) -> Optional[int]:
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, IOError):
            return None
    
    def is_running(self) -> bool:
        pid = self.get_pid()
        if pid is None:
            return False
        
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def start(self, target_func, *args, **kwargs):
        if self.is_running():
            print("LogMonitor is already running")
            sys.exit(1)
        
        if self.pid_file.exists():
            self.pid_file.unlink()
        
        self.daemonize()
        
        self.running = True
        target_func(*args, **kwargs)
    
    def stop(self):
        pid = self.get_pid()
        
        if pid is None:
            print("LogMonitor is not running")
            return
        
        if not self.is_running():
            print("LogMonitor is not running (stale PID)")
            self._cleanup()
            return
        
        try:
            os.kill(pid, signal.SIGTERM)
            
            for _ in range(100):
                if not self.is_running():
                    print("LogMonitor stopped")
                    return
                time.sleep(0.1)
            
            print("Force stopping...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
            
            if not self.is_running():
                print("LogMonitor stopped (forced)")
            else:
                print("Failed to stop LogMonitor")
                
        except OSError as e:
            print(f"Stop error: {e}")
        finally:
            self._cleanup()
    
    def status(self) -> dict:
        pid = self.get_pid()
        running = self.is_running()
        
        status_info = {
            'running': running,
            'pid': pid if running else None,
            'pid_file': str(self.pid_file),
            'log_file': str(self.log_file) if self.log_file else None
        }
        
        return status_info


class LogMonitorDaemon:
    """Main LogMonitor daemon orchestrator."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.running = False
        
        from logmonitor.core.collector import create_collector
        from logmonitor.core.normalizer import create_normalizer
        from logmonitor.core.detector import DetectionEngine
        from logmonitor.storage.database import LogDatabase
        from logmonitor.storage.evidence import EvidenceManager
        from logmonitor.utils.logger import setup_logger
        
        self.logger = setup_logger(
            'logmonitor.daemon',
            self.config.get('general.app_log', '/var/log/logmonitor/app.log'),
            self.config.get('general.log_level', 'INFO')
        )
        
        db_path = self.config.get('storage.database', 'data/logmonitor.db')
        self.db = LogDatabase(db_path)
        
        evidence_dir = self.config.get('storage.evidence_dir', 'data/evidence')
        self.evidence_manager = EvidenceManager(evidence_dir)
        
        self.detector = DetectionEngine(self.config.config)
        self.detector.register_alert_callback(self._handle_alert)
        
        self.collectors = {}
        self.normalizers = {}

        log_paths = self.config.get('logs.paths', [])

        # Auto-inject journald sources if no paths configured / detected
        if not log_paths or all(not p for p in log_paths):
            from logmonitor.utils.linux_detect import is_journald_available
            if is_journald_available():
                self.logger.warning(
                    "No log file paths found — journald detected. "
                    "Auto-adding journald://auth and journald://system."
                )
                log_paths = ['journald://auth', 'journald://system']
            else:
                self.logger.error(
                    "CRITICAL: No log sources found and journald is not available. "
                    "LogMonitor will NOT monitor anything. "
                    "Check your config (logs.paths) or install rsyslog/syslog-ng."
                )

        for log_path in log_paths:
            try:
                is_journald = log_path.startswith('journald://')

                if is_journald:
                    log_type = 'journald'
                elif 'auth' in log_path:
                    log_type = 'auth'
                else:
                    log_type = 'syslog'

                collector = create_collector(log_path)
                normalizer = create_normalizer(log_type)
                self.collectors[log_path] = collector
                self.normalizers[log_path] = normalizer
                self.logger.info(f"Collector initialized: {log_path} (type={log_type})")
            except Exception as e:
                self.logger.error(f"Cannot create collector for {log_path}: {e}")

        if not self.collectors:
            self.logger.error(
                "CRITICAL: No collectors could be initialized. "
                "LogMonitor daemon will start but monitor NOTHING."
            )
        
        pid_file = self.config.get('general.pid_file', '/tmp/logmonitor/logmonitor.pid')
        log_file = self.config.get('general.app_log', '/tmp/logmonitor/app.log')
        self.daemon_process = DaemonProcess(pid_file, log_file)
    
    def get_pid(self):
        return self.daemon_process.get_pid()
    
    def is_running(self):
        return self.daemon_process.is_running()
    
    def start(self):
        self.daemon_process.start(self.run)
    
    def stop(self):
        self.daemon_process.stop()
    
    def _handle_alert(self, alert: dict):
        try:
            alert_id = self.db.insert_alert(alert)
            self.evidence_manager.store_evidence(alert_id, alert)
            
            self.logger.warning(
                f"ALERT [{alert['severity'].upper()}] {alert['rule_name']}: {alert['description']}"
            )
        except Exception as e:
            self.logger.error(f"Alert handling error: {e}")
    
    def _process_log_line(self, raw_line: str, log_path: str):
        try:
            normalizer = self.normalizers[log_path]
            normalized = normalizer.normalize(raw_line)
            
            if normalized:
                self.db.insert_log(normalized)
                self.detector.process_event(normalized)
                
        except Exception as e:
            self.logger.error(f"Line processing error: {e}")
    
    def run(self):
        self.running = True
        self.logger.info("LogMonitor daemon started")
        
        threads = []
        
        for log_path, collector in self.collectors.items():
            callback = lambda line, path=log_path: self._process_log_line(line, path)
            thread = threading.Thread(
                target=collector.collect_streaming,
                args=(callback,),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            self.logger.info(f"Monitoring started for {log_path}")
        
        try:
            while self.running:
                time.sleep(1)
                
                for thread in threads:
                    if not thread.is_alive():
                        self.logger.warning("Monitoring thread died")
        
        except KeyboardInterrupt:
            self.logger.info("Stop requested")
        finally:
            self.running = False
            self.db.close()
            self.logger.info("LogMonitor daemon stopped")

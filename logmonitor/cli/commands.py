"""CLI interface for LogMonitor."""

import click
import sys
import os
from pathlib import Path
from logmonitor.utils.config import get_config

@click.group()
@click.version_option(version='0.1.0', prog_name='LogMonitor')
def cli():
    """LogMonitor - Linux log monitoring and security analysis tool."""
    pass

@cli.command()
@click.option('--config', '-c', help='Path to config file')
def start(config):
    """Start the LogMonitor daemon."""
    try:
        from logmonitor.utils.daemon import LogMonitorDaemon
        cfg = get_config(config)
        daemon = LogMonitorDaemon(cfg)
        
        if daemon.is_running():
            click.echo("[!] Daemon is already running")
            sys.exit(1)
        
        click.echo("[*] Starting LogMonitor daemon...")
        daemon.start()
        click.echo(f"[+] Daemon started (PID: {daemon.get_pid()})")
        
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--config', '-c', help='Path to config file')
def stop(config):
    """Stop the LogMonitor daemon."""
    try:
        from logmonitor.utils.daemon import LogMonitorDaemon
        cfg = get_config(config)
        daemon = LogMonitorDaemon(cfg)
        
        if not daemon.is_running():
            click.echo("[!] Daemon is not running")
            sys.exit(1)
        
        click.echo("[*] Stopping daemon...")
        daemon.stop()
        click.echo("[+] Daemon stopped")
        
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--config', '-c', help='Path to config file')
def status(config):
    """Show daemon status."""
    try:
        from logmonitor.utils.daemon import LogMonitorDaemon
        cfg = get_config(config)
        daemon = LogMonitorDaemon(cfg)
        
        if daemon.is_running():
            click.echo(f"[+] Daemon is running (PID: {daemon.get_pid()})")
        else:
            click.echo("[-] Daemon is not running")
            
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--file', '-f', required=True, help='Log file to analyze')
@click.option('--config', '-c', help='Path to config file')
def scan(file, config):
    """Analyze a log file (one-shot scan)."""
    try:
        from logmonitor.core.collector import create_collector
        from logmonitor.core.normalizer import create_normalizer
        from logmonitor.core.detector import DetectionEngine
        from logmonitor.storage.database import LogDatabase
        
        cfg = get_config(config)
        log_file = Path(file)
        
        if not log_file.exists():
            click.echo(f"[-] File not found: {file}", err=True)
            sys.exit(1)
        
        click.echo(f"[*] Scanning: {file}")
        collector = create_collector(str(log_file))
        
        filename = str(log_file).lower()
        auth_keywords = ['auth', 'ssh', 'login', 'account', 'root', 'modification']
        norm_type = 'auth' if any(k in filename for k in auth_keywords) else 'syslog'
        normalizer = create_normalizer(norm_type)
        
        detector = DetectionEngine(cfg)
        db = LogDatabase(cfg.get('storage.database', 'data/logmonitor.db'))
        
        click.echo(f"[*] Normalizer: {norm_type.upper()}")
        
        BATCH_SIZE = 1000
        batch_logs = []
        total_logs = 0
        total_alerts = 0
        
        iterator = collector.collect_batch()
        
        with click.progressbar(iterator, label='Processing', show_pos=True) as bar:
            for raw in bar:
                norm = normalizer.normalize(raw)
                if norm:
                    batch_logs.append(norm)
                    total_logs += 1
                
                if len(batch_logs) >= BATCH_SIZE:
                    for log in batch_logs:
                        db.insert_log(log)
                    
                    alerts = detector.process_batch(batch_logs)
                    for alert in alerts:
                        db.insert_alert(alert)
                        total_alerts += 1
                    batch_logs = []
            
            if batch_logs:
                for log in batch_logs:
                    db.insert_log(log)
                alerts = detector.process_batch(batch_logs)
                for alert in alerts:
                    db.insert_alert(alert)
                    total_alerts += 1
        
        click.echo(f"\n[+] Scan complete: {total_logs} logs analyzed")
        click.echo(f"[+] {total_alerts} alerts detected")
        db.close()
        
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)
        sys.exit(1)

@cli.group()
def alerts():
    """Alert management."""
    pass

@alerts.command('list')
@click.option('--severity', '-s', help='Filter by severity')
@click.option('--limit', '-l', default=50, help='Number of alerts to show')
@click.option('--config', '-c', help='Path to config file')
def alerts_list(severity, limit, config):
    """List recent alerts."""
    try:
        from logmonitor.storage.database import LogDatabase
        cfg = get_config(config)
        db = LogDatabase(cfg.get('storage.database', 'data/logmonitor.db'))
        
        alerts = db.get_recent_alerts(limit=limit, severity=severity)
        
        if not alerts:
            click.echo("[!] No alerts found")
            sys.exit(0)
        
        click.echo(f"\n[+] {len(alerts)} alerts found:\n")
        
        for alert in alerts:
            severity_color = {
                'low': 'green', 'medium': 'yellow', 'high': 'yellow',
                'critical': 'red', 'emergency': 'magenta'
            }.get(alert['severity'], 'white')
            
            click.secho(f"[{alert['severity'].upper()}] {alert['rule_name']}", fg=severity_color, bold=True)
            click.echo(f"  Timestamp: {alert['timestamp']}")
            click.echo(f"  Description: {alert['description']}")
            if alert.get('source_ip'):
                click.echo(f"  Source IP: {alert['source_ip']}")
            click.echo()
        
        db.close()
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)
        sys.exit(1)

@cli.group()
def report():
    """Report generation."""
    pass

@report.command('generate')
@click.option('--format', '-f', default='pdf', type=click.Choice(['pdf', 'csv']), help='Report format')
@click.option('--output', '-o', help='Output file')
@click.option('--config', '-c', help='Path to config file')
def report_generate(format, output, config):
    """Generate an analysis report."""
    try:
        from logmonitor.reporting.generator import ReportGenerator
        from datetime import datetime
        
        cfg = get_config(config)
        generator = ReportGenerator(cfg)
        
        click.echo(f"[*] Generating {format.upper()} report...")
        
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"reports/report_{timestamp}.{format}"
        
        report_path = generator.generate_report(output_file=output, report_format=format)
        click.echo(f"[+] Report generated: {report_path}")
        
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)
        sys.exit(1)

@cli.group()
def config():
    """Configuration management."""
    pass

@cli.command()
@click.option('--force', is_flag=True, help="Skip confirmation")
@click.option('--config', '-c', help='Path to config file')
@click.pass_context
def clean(ctx, force, config):
    """Clear database (logs and alerts)."""
    cfg = get_config(config)
    
    if not force:
        if not click.confirm("This will delete ALL logs and alerts. Continue?"):
            return
    
    try:
        from logmonitor.storage.database import LogDatabase
        db_path = cfg.get('storage.database', 'data/logmonitor.db')
        db = LogDatabase(db_path)
        db.clear_all()
        db.close()
        click.echo("[+] Database cleared")
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)

@cli.command()
@click.option('--config', '-c', help='Path to config file')
def config_validate(config):
    """Validate config file."""
    try:
        cfg = get_config(config)
        click.echo(f"[+] Config valid: {cfg.config_path}")
        click.echo(f"    - Database: {cfg.get('storage.database')}")
    except Exception as e:
        click.echo(f"[-] Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--port', '-p', default=5000, help='Web server port')
@click.option('--host', '-h', default='127.0.0.1', help='Web server host')
@click.option('--config', '-c', help='Path to config file')
@click.option('--daemon', '-d', is_flag=True, help='Run in background')
def web(port, host, config, daemon):
    """Launch web dashboard."""
    if daemon:
        import subprocess
        
        log_dir = "/tmp/logmonitor"
        os.makedirs(log_dir, exist_ok=True)
        stdout_log = os.path.join(log_dir, "web_stdout.log")
        stderr_log = os.path.join(log_dir, "web_stderr.log")
        pid_file = os.path.join(log_dir, "web.pid")
        
        cmd = [sys.argv[0], "web", "--port", str(port), "--host", host]
        if config:
            cmd.extend(["--config", config])
        
        click.echo(f"Starting dashboard at http://{host}:{port}...")
        
        try:
            with open(stdout_log, 'w') as out, open(stderr_log, 'w') as err:
                process = subprocess.Popen(cmd, stdout=out, stderr=err, start_new_session=True, cwd=os.getcwd())
                with open(pid_file, 'w') as f:
                    f.write(str(process.pid))
            
            click.echo(f"[+] Dashboard started (PID: {process.pid})")
            click.echo(f"[+] Logs: {stdout_log}")
            sys.exit(0)
        except Exception as e:
            click.echo(f"[-] Error: {e}", err=True)
            sys.exit(1)
            
    click.echo(f"Starting dashboard at http://{host}:{port}...")
    try:
        from logmonitor.web.app import create_app
        cfg = get_config(config)
        app = create_app(cfg)
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()

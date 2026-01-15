"""
Module CLI pour LogMonitor
"""

import click
import sys
import os
from pathlib import Path
from logmonitor.utils.config import get_config

@click.group()
@click.version_option(version='0.1.0', prog_name='LogMonitor')
def cli():
    """LogMonitor - Surveillance et analyse de logs Linux"""
    pass

@cli.command()
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
def start(config):
    """Démarre le daemon LogMonitor en arrière-plan"""
    try:
        from logmonitor.utils.daemon import LogMonitorDaemon
        cfg = get_config(config)
        daemon = LogMonitorDaemon(cfg)
        
        if daemon.is_running():
            click.echo("[!] Le daemon est déjà en cours d'exécution")
            sys.exit(1)
        
        click.echo("[*] Démarrage du daemon LogMonitor...")
        daemon.start()
        click.echo(f"[+] Daemon démarré (PID: {daemon.get_pid()})")
        
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
def stop(config):
    """Arrête le daemon LogMonitor"""
    try:
        from logmonitor.utils.daemon import LogMonitorDaemon
        cfg = get_config(config)
        daemon = LogMonitorDaemon(cfg)
        
        if not daemon.is_running():
            click.echo("[!] Le daemon n'est pas en cours d'exécution")
            sys.exit(1)
        
        click.echo("[*] Arrêt du daemon...")
        daemon.stop()
        click.echo("[+] Daemon arrêté")
        
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
def status(config):
    """Affiche le statut du daemon"""
    try:
        from logmonitor.utils.daemon import LogMonitorDaemon
        cfg = get_config(config)
        daemon = LogMonitorDaemon(cfg)
        
        if daemon.is_running():
            click.echo(f"[+] Le daemon est en cours d'exécution (PID: {daemon.get_pid()})")
        else:
            click.echo("[-] Le daemon n'est pas en cours d'exécution")
            
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--file', '-f', required=True, help='Fichier de log à scanner')
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
def scan(file, config):
    """Scanne un fichier de log et détecte les anomalies"""
    try:
        from logmonitor.core.collector import create_collector
        from logmonitor.core.normalizer import create_normalizer
        from logmonitor.core.detector import DetectionEngine
        from logmonitor.storage.database import LogDatabase
        
        cfg = get_config(config)
        log_file = Path(file)
        
        if not log_file.exists():
            click.echo(f"[-] Fichier non trouvé: {file}", err=True)
            sys.exit(1)
        
        click.echo(f"[*] Scan du fichier: {file}")
        # Initialiser les composants
        collector = create_collector(str(log_file))
        
        # Détermination du type de normaliseur
        # On utilise AuthLogNormalizer pour les fichiers contenant 'auth', 'ssh', etc.
        filename = str(log_file).lower()
        auth_keywords = ['auth', 'ssh', 'login', 'account', 'root', 'modification']
        norm_type = 'auth' if any(k in filename for k in auth_keywords) else 'syslog'
        normalizer = create_normalizer(norm_type)
        
        detector = DetectionEngine(cfg)
        db = LogDatabase(cfg.get('storage.database', 'data/logmonitor.db'))
        
        click.echo(f"[*] Mode de normalisation: {norm_type.upper()}")
        
        BATCH_SIZE = 1000
        batch_logs = []
        total_logs = 0
        total_alerts = 0
        
        iterator = collector.collect_batch()
        
        with click.progressbar(iterator, label='Traitement des logs', show_pos=True) as bar:
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
        
        click.echo(f"\n[+] Scan terminé: {total_logs} logs analysés")
        click.echo(f"[+] {total_alerts} alertes détectées")
        db.close()
        
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)
        sys.exit(1)

@cli.group()
def alerts():
    """Gestion des alertes"""
    pass

@alerts.command('list')
@click.option('--severity', '-s', help='Filtrer par sévérité')
@click.option('--limit', '-l', default=50, help='Nombre d\'alertes à afficher')
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
def alerts_list(severity, limit, config):
    """Liste les alertes"""
    try:
        from logmonitor.storage.database import LogDatabase
        cfg = get_config(config)
        db = LogDatabase(cfg.get('storage.database', 'data/logmonitor.db'))
        
        alerts = db.get_recent_alerts(limit=limit, severity=severity)
        
        if not alerts:
            click.echo("[!] Aucune alerte trouvée")
            sys.exit(0)
        
        click.echo(f"\n[+] {len(alerts)} alertes trouvées:\n")
        
        for alert in alerts:
            severity_color = {
                'low': 'green', 'medium': 'yellow', 'high': 'yellow',
                'critical': 'red', 'emergency': 'magenta'
            }.get(alert['severity'], 'white')
            
            click.secho(f"[{alert['severity'].upper()}] {alert['rule_name']}", fg=severity_color, bold=True)
            click.echo(f"  Timestamp: {alert['timestamp']}")
            click.echo(f"  Description: {alert['description']}")
            if alert.get('source_ip'):
                click.echo(f"  IP source: {alert['source_ip']}")
            click.echo()
        
        db.close()
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)
        sys.exit(1)

@cli.group()
def report():
    """Génération de rapports"""
    pass

@report.command('generate')
@click.option('--format', '-f', default='pdf', type=click.Choice(['pdf', 'csv']), help='Format du rapport')
@click.option('--output', '-o', help='Fichier de sortie')
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
def report_generate(format, output, config):
    """Génère un rapport d'analyse"""
    try:
        from logmonitor.reporting.generator import ReportGenerator
        from datetime import datetime
        
        cfg = get_config(config)
        generator = ReportGenerator(cfg)
        
        click.echo(f"[*] Génération du rapport {format.upper()}...")
        
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"reports/report_{timestamp}.{format}"
        
        report_path = generator.generate_report(output_file=output, report_format=format)
        click.echo(f"[+] Rapport généré: {report_path}")
        
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)
        sys.exit(1)

@cli.group()
def config():
    """Gestion de la configuration"""
    pass

@cli.command()
@click.option('--force', is_flag=True, help="Ne demande pas confirmation")
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
@click.pass_context
def clean(ctx, force, config):
    """Vide la base de données (logs et alertes)"""
    cfg = get_config(config)
    
    if not force:
        if not click.confirm("Attention: Cela va supprimer TOUS les logs et alertes. Continuer ?"):
            return
    
    try:
        from logmonitor.storage.database import LogDatabase
        db_path = cfg.get('storage.database', 'data/logmonitor.db')
        db = LogDatabase(db_path)
        db.clear_all()
        db.close()
        click.echo("[+] Base de données nettoyée avec succès")
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)

@cli.command()
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
def config_validate(config):
    """Valide le fichier de configuration"""
    try:
        cfg = get_config(config)
        click.echo(f"[+] Configuration valide: {cfg.config_path}")
        click.echo(f"    - Base de données: {cfg.get('storage.database')}")
    except Exception as e:
        click.echo(f"[-] Erreur: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--port', '-p', default=5000, help='Port du serveur web')
@click.option('--host', '-h', default='127.0.0.1', help='Hôte du serveur web')
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
@click.option('--daemon', '-d', is_flag=True, help='Lancer en arrière-plan')
def web(port, host, config, daemon):
    """Lance le dashboard web"""
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
        
        click.echo(f"Lancement du dashboard en arrière-plan sur http://{host}:{port}...")
        
        try:
            with open(stdout_log, 'w') as out, open(stderr_log, 'w') as err:
                process = subprocess.Popen(cmd, stdout=out, stderr=err, start_new_session=True, cwd=os.getcwd())
                with open(pid_file, 'w') as f:
                    f.write(str(process.pid))
            
            click.echo(f"[+] Dashboard lancé (PID: {process.pid})")
            click.echo(f"[+] Logs: {stdout_log}")
            sys.exit(0)
        except Exception as e:
            click.echo(f"[-] Erreur: {e}", err=True)
            sys.exit(1)
            
    click.echo(f"Démarrage du dashboard web sur http://{host}:{port}...")
    try:
        from logmonitor.web.app import create_app
        cfg = get_config(config)
        app = create_app(cfg)
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()

if __name__ == '__main__':
    cli()

@click.command()
@click.option('--port', '-p', default=5000, help='Port du serveur web')
@click.option('--host', '-h', default='127.0.0.1', help='Hote du serveur web')
@click.option('--config', '-c', help='Chemin vers le fichier de configuration')
@click.option('--daemon', '-d', is_flag=True, help='Lancer en arriere-plan')
def web(port, host, config, daemon):
    """
    Lance le dashboard web
    
    \b
    Demarre un serveur Flask pour visualiser les alertes
    et statistiques en temps reel via une interface web.
    
    \b
    FONCTIONNALITES DU DASHBOARD
    ────────────────────────────
      - KPIs en temps reel (logs, alertes, critiques)
      - Graphiques interactifs (Chart.js)
      - Liste des dernieres alertes
      - Top 10 IPs suspectes
      - Rafraichissement automatique (5 secondes)
    
    \b
    EXEMPLES
    ────────
      # Lancer sur le port par defaut (5000)
      logmonitor web
      
      # Lancer en arriere-plan
      logmonitor web --daemon
      
      # Lancer sur un port personnalisé
      logmonitor web --port 8080
      
      # Accessible depuis le reseau
      logmonitor web --host 0.0.0.0 --port 8080
    
    \b
    ACCES
    ─────
      URL par defaut : http://127.0.0.1:5000
      
      Arret : Ctrl+C dans le terminal (ou kill PID si daemon)
    
    \b
    NOTE
    ────
      Le dashboard lit les donnees de la base SQLite.
      Lancez d'abord 'logmonitor start' ou 'logmonitor scan'
      pour avoir des donnees a visualiser.
    """
    if daemon:
        import subprocess
        import sys
        import os
        
        # We need to call the command again without --daemon
        # We use sys.argv[0] which is the script name (logmonitor)
        cmd = [sys.argv[0], "web", "--port", str(port), "--host", host]
        if config:
            cmd.extend(["--config", config])
        
        click.echo(f"Lancement du dashboard en arriere-plan sur http://{host}:{port}...")
        
        try:
            if os.name == 'posix':
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            else:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            
            click.echo(f"[+] Dashboard lance en background.")
            sys.exit(0)
        except Exception as e:
            click.echo(f"[-] Erreur lors du lancement en background: {e}", err=True)
            sys.exit(1)
            
    click.echo(f"Demarrage du dashboard web sur http://{host}:{port}...")
    
    try:
        from logmonitor.web.app import create_app
        
        cfg = get_config(config)
        app = create_app(cfg)
        app.run(host=host, port=port, debug=True, use_reloader=False)
        
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)

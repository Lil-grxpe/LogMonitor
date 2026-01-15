"""
Application Dashboard Web
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, send_file
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
import json
import subprocess
import os

def create_app(config_manager=None):
    """Crée et configure l'application Flask"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'logmonitor-secret-key-2026'
    
    from logmonitor.storage.database import LogDatabase
    from logmonitor.utils.config import get_config
    
    if config_manager is None:
        config_manager = get_config()
    
    db_path = config_manager.get('storage.database', 'data/logmonitor.db')
    
    credentials_file = Path('config/credentials.yaml')
    if credentials_file.exists():
        import yaml
        with open(credentials_file, 'r') as f:
            creds = yaml.safe_load(f)
            USERS = creds.get('users', {'admin': 'logmonitor123'})
    else:
        USERS = {'admin': 'logmonitor123'}
    
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username in USERS and USERS[username] == password:
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='Identifiants incorrects')
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        session.pop('username', None)
        return redirect(url_for('login'))
    
    @app.route('/')
    @login_required
    def index():
        return render_template('index.html', username=session.get('username'))
    
    @app.route('/api/stats')
    @login_required
    def api_stats():
        try:
            db = LogDatabase(db_path)
            stats = db.get_statistics()
            db.close()
            return jsonify({'success': True, 'data': stats})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/alerts/latest')
    def api_latest_alerts():
        try:
            limit = request.args.get('limit', 50, type=int)
            severity = request.args.get('severity', None)
            
            db = LogDatabase(db_path)
            alerts = db.get_recent_alerts(limit=limit, severity=severity)
            db.close()
            return jsonify({'success': True, 'data': alerts, 'count': len(alerts)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/alerts/by-hour')
    def api_alerts_by_hour():
        try:
            db = LogDatabase(db_path)
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            alerts = db.get_alerts_by_date_range(start_date.isoformat(), end_date.isoformat())
            db.close()
            
            hourly_data = {}
            for alert in alerts:
                try:
                    timestamp = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                    hour = timestamp.strftime('%H:00')
                    hourly_data[hour] = hourly_data.get(hour, 0) + 1
                except:
                    pass
            
            labels = []
            data = []
            for hour in range(24):
                hour_str = f"{hour:02d}:00"
                labels.append(hour_str)
                data.append(hourly_data.get(hour_str, 0))
            
            return jsonify({'success': True, 'labels': labels, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/alerts/by-severity')
    def api_alerts_by_severity():
        try:
            db = LogDatabase(db_path)
            stats = db.get_statistics()
            db.close()
            severity_data = stats.get('alerts_by_severity', {})
            return jsonify({'success': True, 'labels': list(severity_data.keys()), 'data': list(severity_data.values())})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/top-ips')
    def api_top_ips():
        try:
            db = LogDatabase(db_path)
            stats = db.get_statistics()
            db.close()
            return jsonify({'success': True, 'data': stats.get('top_suspicious_ips', [])})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/alerts')
    @login_required
    def alerts_page():
        return render_template('alerts.html')
    
    @app.route('/api/reports/generate', methods=['POST'])
    @login_required
    def api_generate_report():
        try:
            report_format = request.json.get('format', 'pdf')
            root_dir = Path(__file__).resolve().parent.parent.parent
            reports_dir = root_dir / 'reports'
            reports_dir.mkdir(exist_ok=True)
            
            result = subprocess.run(
                ['logmonitor', 'report', 'generate', '--format', report_format],
                cwd=str(root_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                files = list(reports_dir.glob(f'*.{report_format}'))
                if files:
                    report_file = max(files, key=lambda x: x.stat().st_mtime)
                    return jsonify({'success': True, 'filename': report_file.name, 'message': 'Rapport généré'})
                return jsonify({'success': False, 'error': 'Fichier non trouvé'}), 500
            return jsonify({'success': False, 'error': result.stderr}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/reports/download/<filename>')
    @login_required
    def api_download_report(filename):
        try:
            root_dir = Path(__file__).resolve().parent.parent.parent
            reports_dir = root_dir / 'reports'
            file_path = reports_dir / filename
            
            if not file_path.exists():
                return jsonify({'error': 'Fichier non trouvé'}), 404
            return send_file(str(file_path), as_attachment=True)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

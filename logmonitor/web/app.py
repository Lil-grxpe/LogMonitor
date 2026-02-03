"""Flask web dashboard for LogMonitor."""

import os
import yaml
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, send_file
from functools import wraps


def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.urandom(24)
    app.config['CONFIG'] = config
    
    from logmonitor.storage.database import LogDatabase
    
    def get_db():
        db_path = config.get('storage.database', 'data/logmonitor.db')
        return LogDatabase(db_path)
    
    def load_credentials():
        creds_path = config.config_path.parent / 'credentials.yaml'
        if creds_path.exists():
            with open(creds_path, 'r') as f:
                return yaml.safe_load(f)
        return {'users': {'admin': {'password': 'admin', 'role': 'admin'}}}
    
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/')
    @login_required
    def index():
        db = get_db()
        stats = db.get_statistics()
        db.close()
        return render_template('dashboard.html', stats=stats)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            credentials = load_credentials()
            users = credentials.get('users', {})
            
            if username in users and users[username].get('password') == password:
                session['user'] = username
                session['role'] = users[username].get('role', 'user')
                return redirect(url_for('index'))
            
            return render_template('login.html', error='Invalid credentials')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
    
    @app.route('/api/statistics')
    @login_required
    def api_statistics():
        try:
            db = get_db()
            stats = db.get_statistics()
            db.close()
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/alerts')
    @login_required
    def api_alerts():
        try:
            severity = request.args.get('severity')
            limit = request.args.get('limit', 100, type=int)
            
            db = get_db()
            alerts = db.get_recent_alerts(limit=limit, severity=severity)
            db.close()
            
            return jsonify(alerts)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
    @login_required
    def api_acknowledge_alert(alert_id):
        try:
            db = get_db()
            db.acknowledge_alert(alert_id)
            db.close()
            return jsonify({'success': True, 'alert_id': alert_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/reports')
    @login_required
    def reports():
        return render_template('reports.html')
    
    @app.route('/api/reports/generate', methods=['POST'])
    @login_required
    def api_generate_report():
        try:
            from logmonitor.reporting.generator import ReportGenerator
            
            report_format = request.json.get('format', 'pdf')
            generator = ReportGenerator(config)
            report_path = generator.generate_report(report_format=report_format)
            
            return jsonify({
                'success': True,
                'report_path': report_path,
                'download_url': f'/reports/download/{Path(report_path).name}'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/reports/download/<filename>')
    @login_required
    def download_report(filename):
        reports_dir = Path(config.get('reporting.output_dir', 'reports'))
        file_path = reports_dir / filename
        
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    
    @app.route('/settings')
    @login_required
    def settings():
        message = request.args.get('message')
        message_type = request.args.get('type', 'info')
        return render_template('settings.html', config=config.config, message=message, message_type=message_type)

    @app.route('/settings/password', methods=['POST'])
    @login_required
    def change_password():
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        creds_path = config.config_path.parent / 'credentials.yaml'
        credentials = load_credentials()
        username = session['user']
        
        user_data = credentials.get('users', {}).get(username)
        
        if not user_data or user_data.get('password') != current_password:
            return redirect(url_for('settings', message='Mot de passe actuel incorrect', type='danger'))
        
        if new_password != confirm_password:
            return redirect(url_for('settings', message='Les nouveaux mots de passe ne correspondent pas', type='danger'))
            
        if len(new_password) < 8:
             return redirect(url_for('settings', message='Le mot de passe doit faire au moins 8 caractères', type='danger'))

        # Update password
        credentials['users'][username]['password'] = new_password
        
        with open(creds_path, 'w') as f:
            yaml.dump(credentials, f)
            
        return redirect(url_for('settings', message='Mot de passe mis à jour avec succès', type='success'))
    
    return app


def run_server(config, host='127.0.0.1', port=5000, debug=False):
    """Run Flask development server."""
    app = create_app(config)
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    from logmonitor.utils.config import get_config
    cfg = get_config()
    run_server(cfg)

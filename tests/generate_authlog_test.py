#!/usr/bin/env python3
"""
Générateur de fichier authlog de test
Génère 10,000 lignes couvrant toutes les règles de détection
"""

import random
from datetime import datetime, timedelta
from pathlib import Path


class AuthLogGenerator:
    """Générateur de logs d'authentification pour tests"""
    
    def __init__(self):
        self.ips_malicious = [
            "192.168.1.100", "10.0.0.50", "172.16.0.25",
            "203.0.113.45", "198.51.100.78", "192.0.2.123"
        ]
        self.ips_normal = [
            "192.168.1.10", "192.168.1.20", "10.0.0.5"
        ]
        self.usernames = [
            "alice", "bob", "charlie", "david", "eve",
            "admin", "root", "user", "test", "backup"
        ]
        self.sensitive_files = [
            "/etc/passwd", "/etc/shadow", "/etc/sudoers",
            "/etc/ssh/sshd_config", "/root/.ssh/authorized_keys",
            "/etc/security/access.conf"
        ]
        
    def generate_timestamp(self, base_time, offset_minutes=0):
        """Génère un timestamp au format authlog"""
        time = base_time + timedelta(minutes=offset_minutes)
        return time.strftime("%b %d %H:%M:%S")
    
    def generate_ssh_failed_password(self, timestamp, ip, username, hostname="server"):
        """Génère une ligne de tentative SSH échouée"""
        port = random.randint(40000, 60000)
        return f"{timestamp} {hostname} sshd[{random.randint(1000, 9999)}]: Failed password for {username} from {ip} port {port} ssh2\n"
    
    def generate_ssh_invalid_user(self, timestamp, ip, username, hostname="server"):
        """Génère une ligne d'utilisateur invalide SSH"""
        port = random.randint(40000, 60000)
        return f"{timestamp} {hostname} sshd[{random.randint(1000, 9999)}]: Invalid user {username} from {ip} port {port}\n"
    
    def generate_ssh_accepted(self, timestamp, ip, username, hostname="server"):
        """Génère une ligne de connexion SSH réussie"""
        port = random.randint(40000, 60000)
        return f"{timestamp} {hostname} sshd[{random.randint(1000, 9999)}]: Accepted password for {username} from {ip} port {port} ssh2\n"
    
    def generate_root_login(self, timestamp, ip, hostname="server"):
        """Génère une ligne de connexion root suspecte"""
        port = random.randint(40000, 60000)
        return f"{timestamp} {hostname} sshd[{random.randint(1000, 9999)}]: Accepted password for root from {ip} port {port} ssh2\n"
    
    def generate_sudo_command(self, timestamp, username, command, hostname="server"):
        """Génère une ligne de commande sudo"""
        return f"{timestamp} {hostname} sudo: {username} : TTY=pts/0 ; PWD=/home/{username} ; USER=root ; COMMAND={command}\n"
    
    def generate_file_modification(self, timestamp, username, filepath, hostname="server"):
        """Génère une ligne de modification de fichier sensible"""
        # Simuler via audit ou via commande
        if random.choice([True, False]):
            return f"{timestamp} {hostname} audit[{random.randint(1000, 9999)}]: type=SYSCALL msg=audit({int(datetime.now().timestamp())}.{random.randint(100, 999)}:123): arch=c000003e syscall=2 success=yes exit=3 a0=7fffc file={filepath}\n"
        else:
            return f"{timestamp} {hostname} sudo: {username} : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/usr/bin/vi {filepath}\n"
    
    def generate_normal_login(self, timestamp, ip, username, hostname="server"):
        """Génère une ligne de login normal"""
        return f"{timestamp} {hostname} login[{random.randint(1000, 9999)}]: pam_unix(login:session): session opened for user {username} by LOGIN(uid=0)\n"
    
    def generate_cron_log(self, timestamp, username, hostname="server"):
        """Génère une ligne de log cron"""
        return f"{timestamp} {hostname} CRON[{random.randint(1000, 9999)}]: ({username}) CMD (/usr/bin/some-script.sh)\n"
    
    def generate_test_log(self, output_file, total_lines=10000):
        """
        Génère un fichier de test avec environ 10,000 lignes
        
        Répartition approximative:
        - 30% : Logs normaux (connexions réussies, cron, etc.)
        - 25% : Brute-force SSH (failed passwords)
        - 15% : Attaques multi-comptes (invalid users)
        - 10% : Logins root suspects
        - 15% : Modifications de fichiers sensibles
        - 5%  : Pics d'activité (rafales de connexions)
        """
        print(f"Génération de {total_lines} lignes de logs de test...")
        
        base_time = datetime.now() - timedelta(days=7)
        logs = []
        
        # 1. Logs normaux (3000 lignes)
        print("Génération de logs normaux...")
        for i in range(3000):
            timestamp = self.generate_timestamp(base_time, i * 2)
            username = random.choice(self.usernames[:5])  # Utilisateurs légitimes
            ip = random.choice(self.ips_normal)
            
            log_type = random.choice(['login', 'ssh_success', 'cron'])
            if log_type == 'login':
                logs.append(self.generate_normal_login(timestamp, ip, username))
            elif log_type == 'ssh_success':
                logs.append(self.generate_ssh_accepted(timestamp, ip, username))
            else:
                logs.append(self.generate_cron_log(timestamp, username))
        
        # 2. Brute-force SSH (2500 lignes)
        print("Génération d'attaques brute-force SSH...")
        for i in range(2500):
            timestamp = self.generate_timestamp(base_time, i * 2 + 10)
            ip = random.choice(self.ips_malicious)
            username = random.choice(self.usernames)
            logs.append(self.generate_ssh_failed_password(timestamp, ip, username))
        
        # 3. Attaques multi-comptes (1500 lignes)
        print("Génération d'attaques multi-comptes...")
        for i in range(1500):
            timestamp = self.generate_timestamp(base_time, i * 3 + 50)
            ip = random.choice(self.ips_malicious)
            # Utilisateurs invalides/suspects
            fake_users = ["admin123", "test", "oracle", "mysql", "postgres", "guest", "ftpuser"]
            username = random.choice(fake_users)
            logs.append(self.generate_ssh_invalid_user(timestamp, ip, username))
        
        # 4. Logins root suspects (1000 lignes)
        print("Génération de logins root suspects...")
        for i in range(1000):
            timestamp = self.generate_timestamp(base_time, i * 5 + 100)
            ip = random.choice(self.ips_malicious)
            logs.append(self.generate_root_login(timestamp, ip))
        
        # 5. Modifications fichiers sensibles (1500 lignes)
        print("Génération de modifications de fichiers sensibles...")
        for i in range(1500):
            timestamp = self.generate_timestamp(base_time, i * 4 + 200)
            username = random.choice(["root", "admin", "backup"])
            filepath = random.choice(self.sensitive_files)
            logs.append(self.generate_file_modification(timestamp, username, filepath))
        
        # 6. Pics d'activité - rafales de connexions (500 lignes)
        print("Génération de pics d'activité...")
        spike_time = self.generate_timestamp(base_time, 5000)
        ip = random.choice(self.ips_malicious)
        for i in range(500):
            # Toutes les tentatives dans la même minute
            logs.append(self.generate_ssh_failed_password(spike_time, ip, random.choice(self.usernames)))
        
        # Mélanger tous les logs pour plus de réalisme
        print("Mélange des logs...")
        random.shuffle(logs)
        
        # Écrire dans le fichier
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Écriture dans {output_file}...")
        with open(output_file, 'w') as f:
            f.writelines(logs)
        
        print(f"✓ Fichier généré : {output_file}")
        print(f"✓ Total de lignes : {len(logs)}")
        print(f"\nStatistiques:")
        print(f"  - Logs normaux : ~3000")
        print(f"  - Brute-force SSH : ~2500")
        print(f"  - Multi-comptes : ~1500")
        print(f"  - Root suspects : ~1000")
        print(f"  - Fichiers sensibles : ~1500")
        print(f"  - Pics d'activité : ~500")


if __name__ == "__main__":
    generator = AuthLogGenerator()
    output = "tests/authlog_test.log"
    generator.generate_test_log(output, total_lines=10000)

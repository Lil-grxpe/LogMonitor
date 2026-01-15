#!/usr/bin/env python3
"""
Script de génération de scénarios de logs volumineux pour LogMonitor.
Génère 6 fichiers de logs simulant différents types de trafic et d'attaques,
mélangés à du bruit de fond (trafic légitime).
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
import os

# Configuration
OUTPUT_DIR = Path("tests/test_logs")
LOGS_PER_FILE = 800  # Nombre total de lignes par fichier
ATTACK_INTENSITY = 0.1  # 10% des logs sont des attaques
START_TIME = datetime.now() - timedelta(hours=2)

# Templates de logs légitimes (Bruit de fond)
NORMAL_LOGS = [
    "Accepted publickey for admin from 192.168.1.{ip} port {port} ssh2",
    "Accepted password for user{u} from 10.0.0.{ip} port {port} ssh2",
    "Disconnected from user{u} 10.0.0.{ip} port {port}",
    "pam_unix(sshd:session): session opened for user admin by (uid=0)",
    "pam_unix(sshd:session): session closed for user admin",
    "CRON[1234]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "CRON[1234]: pam_unix(cron:session): session closed for user root",
    "systemd: Started Session {s} of user user{u}.",
    "systemd: Reached target Graphical Interface.",
    "kernel: [123456.789012] cfg80211: Loading compiled-in X.509 certificates for regulatory database",
    "dhclient[123]: DHCPREQUEST for 192.168.1.{ip} on eth0 to 192.168.1.1 port 67",
    "dhclient[123]: DHCPACK of 192.168.1.{ip} from 192.168.1.1",
    "named[987]: client @0x7f... 192.168.1.{ip}#54321 (google.com): query: google.com IN A + (192.168.1.1)"
]

def generate_timestamp(base_time, offset_seconds):
    dt = base_time + timedelta(seconds=offset_seconds)
    # Format syslog standard : Jan 01 12:34:56
    return dt.strftime("%b %d %H:%M:%S")

def get_random_ip():
    return f"{random.randint(1,254)}"

def get_random_port():
    return f"{random.randint(1024, 65535)}"

def write_log(f, timestamp, hostname, process, message):
    f.write(f"{timestamp} {hostname} {process}: {message}\n")

def generate_scenario(filename, scenario_type):
    output_path = OUTPUT_DIR / filename
    print(f"[*] Génération de {filename} ({scenario_type})...")
    
    logs = []
    current_time = START_TIME
    
    # Génération du bruit de fond
    for i in range(int(LOGS_PER_FILE * (1 - ATTACK_INTENSITY))):
        template = random.choice(NORMAL_LOGS)
        msg = template.format(
            ip=get_random_ip(),
            port=get_random_port(),
            u=random.randint(1, 5),
            s=random.randint(100, 999)
        )
        logs.append({
            'time': current_time + timedelta(seconds=random.randint(1, 3600)),
            'host': 'server01',
            'proc': f"sshd[{random.randint(1000,9999)}]" if "ssh" in msg else f"systemd[{random.randint(1,999)}]",
            'msg': msg
        })

    # Injection des attaques
    attack_time = current_time + timedelta(minutes=30)
    
    if scenario_type == "bruteforce_ssh":
        attacker_ip = "192.168.56.101"
        target_user = "admin"
        # 20 tentatives échouées en 2 minutes
        for i in range(20):
            logs.append({
                'time': attack_time + timedelta(seconds=i*5),
                'host': 'server01',
                'proc': f"sshd[{random.randint(20000, 29999)}]",
                'msg': f"Failed password for {target_user} from {attacker_ip} port {random.randint(40000,50000)} ssh2"
            })
            
    elif scenario_type == "multiple_accounts":
        attacker_ip = "203.0.113.66"
        users = ["alice", "bob", "charlie", "david", "eve"]
        # Tentatives sur 5 comptes différents
        for i, user in enumerate(users):
            logs.append({
                'time': attack_time + timedelta(seconds=i*10),
                'host': 'db-prod',
                'proc': f"sshd[{random.randint(20000, 29999)}]",
                'msg': f"Failed password for {user} from {attacker_ip} port {random.randint(40000,50000)} ssh2"
            })

    elif scenario_type == "suspicious_root":
        attacker_ip = "45.12.34.56" # IP externe suspecte
        logs.append({
            'time': attack_time,
            'host': 'server01',
            'proc': f"sshd[{random.randint(20000, 29999)}]",
            'msg': f"Accepted password for root from {attacker_ip} port 54322 ssh2"
        })

    elif scenario_type == "sensitive_file":
        user = "www-data"
        target = "root"
        logs.append({
            'time': attack_time,
            'host': 'web01',
            'proc': "sudo",
            'msg': f"{user} : TTY=pts/0 ; PWD=/var/www ; USER={target} ; COMMAND=/usr/bin/vim /etc/shadow"
        })
        
    elif scenario_type == "activity_spike":
        # Générer 500 logs additionnels sur une courte période
        burst_time = attack_time + timedelta(hours=1)
        for i in range(500):
            template = random.choice(NORMAL_LOGS)
            msg = template.format(ip=get_random_ip(), port=get_random_port(), u=random.randint(1,5), s=random.randint(100,999))
            logs.append({
                'time': burst_time + timedelta(milliseconds=i*100), # Très rapide
                'host': 'server01',
                'proc': f"sshd[{random.randint(1000,9999)}]",
                'msg': msg
            })
            
    # Trier par temps
    logs.sort(key=lambda x: x['time'])
    
    # Écriture fichier
    with open(output_path, 'w') as f:
        for log in logs:
            ts = log['time'].strftime("%b %d %H:%M:%S")
            write_log(f, ts, log['host'], log['proc'], log['msg'])

def main():
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
    
    scenarios = [
        ("01_bruteforce_ssh.log", "bruteforce_ssh"),
        ("02_multiple_accounts_attack.log", "multiple_accounts"),
        ("03_suspicious_root_login.log", "suspicious_root"),
        ("04_sensitive_file_modification.log", "sensitive_file"),
        ("05_activity_spike.log", "activity_spike"),
        ("06_normal_activity.log", "normal") # Just background noise
    ]
    
    for filename, type in scenarios:
        generate_scenario(filename, type)
    
    print(f"\n[+] 6 fichiers de logs générés dans {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

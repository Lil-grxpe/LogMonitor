# Guide LogMonitor pour Kali Linux

## 📋 Différences avec les systèmes Linux classiques

Sur **Kali Linux** (basé sur Debian), les logs d'authentification ne sont pas dans `/var/log/auth.log` mais dans le **journal systemd**.

## 🔍 Où trouver les logs sur Kali ?

### Logs d'authentification SSH

```bash
# Voir les logs SSH en temps réel
journalctl -u ssh -f

# Exporter les logs SSH des dernières 24h
journalctl -u ssh --since "24 hours ago" > /tmp/ssh.log

# Exporter tous les logs SSH
journalctl -u ssh --no-pager > /tmp/ssh_all.log
```

### Logs système disponibles

```bash
# Logs dans /var/log/
ls /var/log/

# Logs utiles pour LogMonitor :
# - /var/log/apache2/access.log    # Logs Apache
# - /var/log/nginx/access.log      # Logs Nginx
# - /var/log/mysql/error.log       # Logs MySQL
```

## 🚀 Installation sur Kali

```bash
# 1. Cloner et installer
git clone https://github.com/Lil-grxpe/LogMonitor.git
cd LogMonitor
./install.sh
```

Le script détectera Kali Linux et configurera automatiquement les chemins de logs.

> Après l'installation, LogMonitor est **actif et démarre automatiquement** au boot via systemd.

## 🧪 Utilisation sur Kali

### Option 1 : Analyser les logs systemd (Recommandé)

```bash
# 1. Exporter les logs SSH du journal systemd
journalctl -u ssh --since "7 days ago" --no-pager > /tmp/ssh_logs.log

# 2. Analyser avec LogMonitor
logmonitor scan -f /tmp/ssh_logs.log

# 3. Voir les alertes
logmonitor alerts list
```

### Option 2 : Utiliser les fichiers de test

```bash
logmonitor scan -f tests/test_logs/01_bruteforce_ssh.log
logmonitor scan -f tests/test_logs/02_multiple_accounts_attack.log
logmonitor scan -f tests/test_logs/03_suspicious_root_login.log
```

### Option 3 : Mode daemon avec export automatique

Créer un script pour exporter régulièrement les logs :

```bash
#!/bin/bash
# /usr/local/bin/export_ssh_logs.sh
journalctl -u ssh --since "24 hours ago" --no-pager > /var/log/ssh_export.log
logmonitor scan -f /var/log/ssh_export.log
```

Puis ajouter dans crontab :
```bash
crontab -e
# Ajouter : 0 * * * * /usr/local/bin/export_ssh_logs.sh
```

## 📊 Configuration pour Kali Linux

Modifier `config/logmonitor.yaml` :

```yaml
logs:
  paths:
    - /var/log/ssh_export.log
    - /var/log/apache2/access.log
```

## 💡 Commandes utiles

```bash
# Échecs de connexion SSH
journalctl -u ssh | grep "Failed password"

# Connexions réussies
journalctl -u ssh | grep "Accepted"

# Dernière heure
journalctl -u ssh --since "1 hour ago"
```

## 🔧 Script d'export automatique complet

Créer `/usr/local/bin/logmonitor-export.sh` :

```bash
#!/bin/bash
EXPORT_DIR="/var/log/logmonitor-exports"
mkdir -p "$EXPORT_DIR"

journalctl -u ssh --since "24 hours ago" --no-pager > "$EXPORT_DIR/ssh.log"
journalctl -t sudo --since "24 hours ago" --no-pager > "$EXPORT_DIR/sudo.log"
journalctl -u systemd-logind --since "24 hours ago" --no-pager > "$EXPORT_DIR/auth.log"

echo "Logs exportés dans $EXPORT_DIR"
```

```bash
chmod +x /usr/local/bin/logmonitor-export.sh
```

Configuration LogMonitor adaptée :
```yaml
logs:
  paths:
    - /var/log/logmonitor-exports/ssh.log
    - /var/log/logmonitor-exports/sudo.log
    - /var/log/logmonitor-exports/auth.log
```

## 📝 Notes importantes

1. **Permissions** : Sur Kali, vous devez être root ou dans le groupe `systemd-journal` pour lire les logs :
   ```bash
   sudo usermod -a -G systemd-journal $USER
   newgrp systemd-journal
   ```

2. **Persistance du journal** : Par défaut, le journal systemd est volatile. Pour le rendre persistant :
   ```bash
   sudo mkdir -p /var/log/journal
   sudo systemctl restart systemd-journald
   ```

## 🐛 Dépannage

### « Permission denied » sur journalctl

```bash
# Solution 1 : Utiliser sudo
sudo journalctl -u ssh > /tmp/ssh.log
sudo chown $USER /tmp/ssh.log
logmonitor scan -f /tmp/ssh.log

# Solution 2 : Ajouter au groupe
sudo usermod -a -G systemd-journal $USER
newgrp systemd-journal
```

### Aucun log SSH trouvé

```bash
# Vérifier que SSH est actif
sudo systemctl status ssh

# Démarrer SSH si nécessaire
sudo systemctl start ssh
```

### « logmonitor: command not found »

```bash
source ~/.bashrc
# ou
source ~/.zshrc
```

---

**Auteur** : Équipe LogMonitor  
**Date** : 2026-01-02  
**Version** : 1.1

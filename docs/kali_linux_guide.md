# Guide LogMonitor pour Kali Linux

## 📋 Différences avec les systèmes Linux classiques

Sur **Kali Linux** (basé sur Debian), les logs d'authentification ne sont pas dans `/var/log/auth.log` mais dans le **journal systemd**.

## 🔍 Où trouver les logs sur Kali ?

### Logs d'authentification SSH

Les logs SSH sont dans le journal systemd. Pour les extraire :

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
# Logs disponibles dans /var/log/
ls /var/log/

# Logs utiles pour LogMonitor :
- /var/log/apache2/access.log    # Logs Apache
- /var/log/nginx/access.log       # Logs Nginx  
- /var/log/mysql/error.log        # Logs MySQL
- /var/log/postgresql/            # Logs PostgreSQL
- /var/log/sysstat/               # Statistiques système
```

## 🚀 Utilisation de LogMonitor sur Kali

### Option 1 : Analyser les logs systemd (Recommandé)

```bash
# 1. Exporter les logs SSH du journal systemd
journalctl -u ssh --since "7 days ago" --no-pager > /tmp/ssh_logs.log

# 2. Analyser avec LogMonitor
logmonitor scan /tmp/ssh_logs.log

# 3. Voir les alertes
logmonitor alerts list
```

### Option 2 : Utiliser les fichiers de test

```bash
# Utiliser les fichiers de test fournis
logmonitor scan tests/test_logs/01_bruteforce_ssh.log
logmonitor scan tests/test_logs/02_multiple_accounts_attack.log
logmonitor scan tests/test_logs/03_suspicious_root_login.log
```

### Option 3 : Mode daemon avec export automatique

Créer un script pour exporter régulièrement les logs :

```bash
#!/bin/bash
# /usr/local/bin/export_ssh_logs.sh

# Exporter les logs SSH des dernières 24h
journalctl -u ssh --since "24 hours ago" --no-pager > /var/log/ssh_export.log

# Analyser avec LogMonitor
logmonitor scan /var/log/ssh_export.log
```

Puis ajouter dans crontab :
```bash
# Exporter et analyser toutes les heures
0 * * * * /usr/local/bin/export_ssh_logs.sh
```

## 📊 Configuration pour Kali Linux

Modifier `config/logmonitor.yaml` :

```yaml
logs:
  paths:
    # Utiliser les exports du journal systemd
    - /var/log/ssh_export.log
    # Ou d'autres logs disponibles
    - /var/log/apache2/access.log
    - /var/log/nginx/access.log
```

## 🧪 Test rapide sur Kali

```bash
# 1. Activer l'environnement
source venv/bin/activate

# 2. Exporter les logs SSH
journalctl -u ssh --since "1 day ago" --no-pager > /tmp/test_ssh.log

# 3. Analyser
logmonitor scan /tmp/test_ssh.log

# 4. Voir les résultats
logmonitor alerts list
```

## 💡 Commandes utiles pour Kali

### Voir les tentatives de connexion SSH

```bash
# Échecs de connexion SSH
journalctl -u ssh | grep "Failed password"

# Connexions réussies
journalctl -u ssh | grep "Accepted"

# Dernière heure
journalctl -u ssh --since "1 hour ago"
```

### Générer des logs de test

```bash
# Simuler des tentatives de connexion (pour test)
# ATTENTION : À faire uniquement sur une VM de test !

# Tentative échouée
ssh wronguser@localhost

# Voir immédiatement dans le journal
journalctl -u ssh -n 10
```

## 🔧 Adapter LogMonitor pour le journal systemd

### Script d'export automatique

Créer `/usr/local/bin/logmonitor-export.sh` :

```bash
#!/bin/bash
# Export automatique des logs systemd pour LogMonitor

EXPORT_DIR="/var/log/logmonitor-exports"
mkdir -p "$EXPORT_DIR"

# Export SSH
journalctl -u ssh --since "24 hours ago" --no-pager > "$EXPORT_DIR/ssh.log"

# Export sudo (si disponible)
journalctl -t sudo --since "24 hours ago" --no-pager > "$EXPORT_DIR/sudo.log"

# Export authentification
journalctl -u systemd-logind --since "24 hours ago" --no-pager > "$EXPORT_DIR/auth.log"

echo "Logs exportés dans $EXPORT_DIR"
```

Rendre exécutable :
```bash
chmod +x /usr/local/bin/logmonitor-export.sh
```

### Crontab pour export régulier

```bash
# Éditer crontab
crontab -e

# Ajouter cette ligne (export toutes les heures)
0 * * * * /usr/local/bin/logmonitor-export.sh
```

### Configuration LogMonitor adaptée

```yaml
logs:
  paths:
    - /var/log/logmonitor-exports/ssh.log
    - /var/log/logmonitor-exports/sudo.log
    - /var/log/logmonitor-exports/auth.log
```

## 📝 Notes importantes

1. **Permissions** : Sur Kali, vous devez être root ou dans le groupe `systemd-journal` pour lire les logs
   ```bash
   sudo usermod -a -G systemd-journal $USER
   newgrp systemd-journal
   ```

2. **Format des logs** : Le journal systemd a un format différent. LogMonitor peut nécessiter des ajustements du parser.

3. **Persistance** : Par défaut, le journal systemd est volatile. Pour le rendre persistant :
   ```bash
   sudo mkdir -p /var/log/journal
   sudo systemctl restart systemd-journald
   ```

## 🎯 Workflow recommandé pour Kali

```bash
# 1. Export initial
journalctl -u ssh --since "7 days ago" --no-pager > /tmp/ssh_week.log

# 2. Analyser
logmonitor scan /tmp/ssh_week.log

# 3. Dashboard
logmonitor web --port 5000

# 4. Générer rapport
logmonitor report generate --format pdf
```

## 🐛 Dépannage

### Problème : "Permission denied" sur journalctl

```bash
# Solution 1 : Utiliser sudo
sudo journalctl -u ssh > /tmp/ssh.log
sudo chown $USER /tmp/ssh.log
logmonitor scan /tmp/ssh.log

# Solution 2 : Ajouter au groupe
sudo usermod -a -G systemd-journal $USER
newgrp systemd-journal
```

### Problème : Aucun log SSH trouvé

```bash
# Vérifier que SSH est actif
sudo systemctl status ssh

# Démarrer SSH si nécessaire
sudo systemctl start ssh

# Générer des logs de test
ssh localhost
```

---

**Auteur** : Équipe LogMonitor  
**Date** : 2026-01-02  
**Version** : 1.0

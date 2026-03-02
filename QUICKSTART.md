# Guide de Démarrage Rapide - LogMonitor

## Installation (2 minutes)

```bash
# 1. Cloner et installer
git clone https://github.com/Lil-grxpe/LogMonitor.git
cd LogMonitor
./install.sh
```

C'est tout ! LogMonitor est installé, activé au démarrage, et déjà en cours d'exécution.

## Vérification

```bash
# Vérifier que le service tourne
sudo systemctl status logmonitor

# Vérifier la version
logmonitor --version
```

> Si `logmonitor: command not found`, rechargez votre shell : `source ~/.bashrc`

## Utilisation

### Voir les Alertes

```bash
logmonitor alerts list
logmonitor alerts list --severity high
```

### Analyser un Fichier Manuellement

```bash
logmonitor scan -f /var/log/auth.log
```

### Générer un Rapport

```bash
logmonitor report generate                # PDF (par défaut)
logmonitor report generate --format csv   # CSV
```

### Dashboard Web

```bash
logmonitor web
# Ouvrir http://127.0.0.1:5000
# Identifiants : admin / admin
```

## Gestion du Service

```bash
sudo systemctl status logmonitor     # État
sudo systemctl stop logmonitor       # Arrêter
sudo systemctl restart logmonitor    # Redémarrer
sudo journalctl -u logmonitor -f     # Logs en direct
```

## Permissions

Si vous avez une erreur « Permission denied » :

```bash
sudo usermod -a -G adm $USER
newgrp adm
```

## Documentation Complète

- [Installation détaillée](docs/installation.md)
- [Guide daemon](docs/daemon_guide.md)
- [README](README.md)

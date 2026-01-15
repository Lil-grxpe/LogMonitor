# Guide de Démarrage Rapide - LogMonitor

## Installation (2 minutes)

```bash
# 1. Installer
./install.sh

# 2. Activer l'environnement
source venv/bin/activate

# 3. Tester
logmonitor --version
```

## Utilisation

### Mode Daemon (Surveillance continue)

```bash
# Démarrer
logmonitor start

# Vérifier
logmonitor status

# Arrêter
logmonitor stop
```

### Analyser un Fichier

```bash
logmonitor scan /var/log/auth.log
```

### Voir les Alertes

```bash
logmonitor alerts list
logmonitor alerts list --severity high
```

### Générer un Rapport

```bash
# PDF
logmonitor report generate

# CSV
logmonitor report generate --format csv
```

### Dashboard Web

```bash
logmonitor web
# Ouvrir http://localhost:5000
```

## Commandes Utiles

```bash
# Valider la configuration
logmonitor config validate

# Voir l'aide
logmonitor --help
logmonitor scan --help
```

## Permissions

Si vous avez une erreur "Permission denied" :

```bash
sudo usermod -a -G adm $USER
newgrp adm
```

## Documentation Complète

- [Installation détaillée](docs/installation.md)
- [Guide daemon](docs/daemon_guide.md)
- [README](README.md)
